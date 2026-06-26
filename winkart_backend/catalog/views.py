import uuid
from datetime import datetime, timezone

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from bson import ObjectId

from winkart_backend.database import product_structures_col
from catalog.serializers import (
    TopCategorySerializer,
    AddNodeSerializer,
    RenameNodeSerializer,
    UpdateLevelNameSerializer,
    AddLevelSerializer,
    SetFieldSchemaSerializer,
    ProductStructureSerializer,
)


def _get_structure(seller_id: str):
    """Fetch the seller's product structure document, or None."""
    return product_structures_col.find_one({'seller_id': seller_id})


def _serialize_structure(doc):
    """Convert a MongoDB document to a JSON-safe dict."""
    if not doc:
        return None
    result = {
        'seller_id': doc['seller_id'],
        'top_category': doc.get('top_category'),
        'levels': doc.get('levels', []),
        'created_at': doc.get('created_at', '').isoformat() if doc.get('created_at') else None,
        'updated_at': doc.get('updated_at', '').isoformat() if doc.get('updated_at') else None,
    }
    return result


def _find_node_in_levels(levels, node_id):
    """Search all levels for a node with the given id. Returns (level_index, node_dict) or (None, None)."""
    for level in levels:
        for node in level.get('nodes', []):
            if node['id'] == node_id:
                return level['level_index'], node
    return None, None


def _get_all_descendant_ids(levels, node_id):
    """Recursively collect all descendant node IDs for a given node."""
    descendants = []
    direct_children = []
    for level in levels:
        for node in level.get('nodes', []):
            if node.get('parent_id') == node_id:
                direct_children.append(node['id'])
    for child_id in direct_children:
        descendants.append(child_id)
        descendants.extend(_get_all_descendant_ids(levels, child_id))
    return descendants


class ProductStructureView(APIView):
    """
    GET  /api/catalog/structure/     — Retrieve seller's full product structure.
    POST /api/catalog/structure/     — Initialize or reset top-level category.
    DELETE /api/catalog/structure/   — Wipe the entire structure and start fresh.
    """
    permission_classes = [IsAuthenticated]

    def get(self, request):
        if request.user.role != 'seller':
            return Response({'error': 'Access denied. Sellers only.'}, status=status.HTTP_403_FORBIDDEN)

        doc = _get_structure(request.user.id)
        if not doc:
            return Response({'exists': False, 'structure': None}, status=status.HTTP_200_OK)

        return Response({'exists': True, 'structure': _serialize_structure(doc)}, status=status.HTTP_200_OK)

    def post(self, request):
        """Initialize (or re-initialize) with a top-level category. Wipes existing structure."""
        if request.user.role != 'seller':
            return Response({'error': 'Access denied. Sellers only.'}, status=status.HTTP_403_FORBIDDEN)

        serializer = TopCategorySerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        data = serializer.validated_data
        now = datetime.now(timezone.utc)

        new_doc = {
            'seller_id': request.user.id,
            'top_category': {
                'name': data['name'],
                'icon': data.get('icon', 'grid-outline'),
                'is_preset': data.get('is_preset', False),
            },
            'levels': [],
            'created_at': now,
            'updated_at': now,
        }

        product_structures_col.replace_one(
            {'seller_id': request.user.id},
            new_doc,
            upsert=True
        )

        return Response(
            {'message': 'Product structure initialized.', 'structure': _serialize_structure(new_doc)},
            status=status.HTTP_201_CREATED
        )

    def delete(self, request):
        """Completely wipe the seller's product structure."""
        if request.user.role != 'seller':
            return Response({'error': 'Access denied. Sellers only.'}, status=status.HTTP_403_FORBIDDEN)

        product_structures_col.delete_one({'seller_id': request.user.id})
        return Response({'message': 'Product structure deleted.'}, status=status.HTTP_200_OK)


class LevelView(APIView):
    """
    POST /api/catalog/levels/              — Add a new hierarchy level.
    PUT  /api/catalog/levels/<level_index>/ — Rename a hierarchy level.
    DELETE /api/catalog/levels/<level_index>/ — Delete a level and all its nodes.
    """
    permission_classes = [IsAuthenticated]

    def post(self, request):
        """Add a new level at the end of the hierarchy."""
        if request.user.role != 'seller':
            return Response({'error': 'Access denied. Sellers only.'}, status=status.HTTP_403_FORBIDDEN)

        doc = _get_structure(request.user.id)
        if not doc:
            return Response({'error': 'Product structure not initialized yet.'}, status=status.HTTP_400_BAD_REQUEST)

        serializer = AddLevelSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        level_name = serializer.validated_data['level_name']
        levels = doc.get('levels', [])
        new_level_index = len(levels)

        new_level = {
            'level_index': new_level_index,
            'level_name': level_name,
            'nodes': [],
        }
        levels.append(new_level)

        product_structures_col.update_one(
            {'seller_id': request.user.id},
            {'$set': {'levels': levels, 'updated_at': datetime.now(timezone.utc)}}
        )
        return Response({'message': 'Level added.', 'level': new_level}, status=status.HTTP_201_CREATED)

    def put(self, request, level_index):
        """Rename a hierarchy level."""
        if request.user.role != 'seller':
            return Response({'error': 'Access denied. Sellers only.'}, status=status.HTTP_403_FORBIDDEN)

        doc = _get_structure(request.user.id)
        if not doc:
            return Response({'error': 'Product structure not initialized yet.'}, status=status.HTTP_400_BAD_REQUEST)

        serializer = UpdateLevelNameSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        levels = doc.get('levels', [])
        level_found = False
        for level in levels:
            if level['level_index'] == level_index:
                level['level_name'] = serializer.validated_data['level_name']
                level_found = True
                break

        if not level_found:
            return Response({'error': 'Level not found.'}, status=status.HTTP_404_NOT_FOUND)

        product_structures_col.update_one(
            {'seller_id': request.user.id},
            {'$set': {'levels': levels, 'updated_at': datetime.now(timezone.utc)}}
        )
        return Response({'message': 'Level renamed successfully.'}, status=status.HTTP_200_OK)

    def delete(self, request, level_index):
        """Delete a level and all its nodes (also removes all deeper levels referencing them)."""
        if request.user.role != 'seller':
            return Response({'error': 'Access denied. Sellers only.'}, status=status.HTTP_403_FORBIDDEN)

        doc = _get_structure(request.user.id)
        if not doc:
            return Response({'error': 'Product structure not initialized yet.'}, status=status.HTTP_400_BAD_REQUEST)

        levels = doc.get('levels', [])
        # Keep only levels before this index; drop this one and everything deeper
        new_levels = [l for l in levels if l['level_index'] < level_index]

        product_structures_col.update_one(
            {'seller_id': request.user.id},
            {'$set': {'levels': new_levels, 'updated_at': datetime.now(timezone.utc)}}
        )
        return Response({'message': f'Level {level_index} and all deeper levels removed.'}, status=status.HTTP_200_OK)


class NodeView(APIView):
    """
    POST /api/catalog/nodes/            — Add a node to a specific level.
    PUT  /api/catalog/nodes/<node_id>/  — Rename a node.
    DELETE /api/catalog/nodes/<node_id>/ — Delete a node and its descendants.
    """
    permission_classes = [IsAuthenticated]

    def post(self, request):
        """Add a new category node to the specified level."""
        if request.user.role != 'seller':
            return Response({'error': 'Access denied. Sellers only.'}, status=status.HTTP_403_FORBIDDEN)

        doc = _get_structure(request.user.id)
        if not doc:
            return Response({'error': 'Product structure not initialized yet.'}, status=status.HTTP_400_BAD_REQUEST)

        serializer = AddNodeSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        data = serializer.validated_data
        level_index = data['level_index']
        parent_id = data.get('parent_id')

        levels = doc.get('levels', [])

        # Find target level
        target_level = next((l for l in levels if l['level_index'] == level_index), None)
        if not target_level:
            return Response({'error': f'Level {level_index} does not exist.'}, status=status.HTTP_400_BAD_REQUEST)

        # Validate parent exists (if provided)
        if parent_id is not None:
            parent_level_idx, _ = _find_node_in_levels(levels, parent_id)
            if parent_level_idx is None:
                return Response({'error': f'Parent node "{parent_id}" not found.'}, status=status.HTTP_400_BAD_REQUEST)
            if parent_level_idx != level_index - 1:
                return Response({'error': 'Parent must be in the immediately preceding level.'}, status=status.HTTP_400_BAD_REQUEST)

        new_node = {
            'id': str(uuid.uuid4()),
            'name': data['name'],
            'parent_id': parent_id,
            'field_schema': [],
        }
        target_level['nodes'].append(new_node)

        product_structures_col.update_one(
            {'seller_id': request.user.id},
            {'$set': {'levels': levels, 'updated_at': datetime.now(timezone.utc)}}
        )
        return Response({'message': 'Node added.', 'node': new_node}, status=status.HTTP_201_CREATED)

    def put(self, request, node_id):
        """Rename an existing node."""
        if request.user.role != 'seller':
            return Response({'error': 'Access denied. Sellers only.'}, status=status.HTTP_403_FORBIDDEN)

        doc = _get_structure(request.user.id)
        if not doc:
            return Response({'error': 'Product structure not initialized yet.'}, status=status.HTTP_400_BAD_REQUEST)

        serializer = RenameNodeSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        levels = doc.get('levels', [])
        node_found = False
        for level in levels:
            for node in level.get('nodes', []):
                if node['id'] == node_id:
                    node['name'] = serializer.validated_data['name']
                    node_found = True
                    break
            if node_found:
                break

        if not node_found:
            return Response({'error': 'Node not found.'}, status=status.HTTP_404_NOT_FOUND)

        product_structures_col.update_one(
            {'seller_id': request.user.id},
            {'$set': {'levels': levels, 'updated_at': datetime.now(timezone.utc)}}
        )
        return Response({'message': 'Node renamed successfully.'}, status=status.HTTP_200_OK)

    def delete(self, request, node_id):
        """Delete a node and cascade-delete all its children."""
        if request.user.role != 'seller':
            return Response({'error': 'Access denied. Sellers only.'}, status=status.HTTP_403_FORBIDDEN)

        doc = _get_structure(request.user.id)
        if not doc:
            return Response({'error': 'Product structure not initialized yet.'}, status=status.HTTP_400_BAD_REQUEST)

        levels = doc.get('levels', [])

        # Collect all IDs to remove (node + descendants)
        ids_to_remove = {node_id}
        ids_to_remove.update(_get_all_descendant_ids(levels, node_id))

        node_found = False
        for level in levels:
            original_count = len(level.get('nodes', []))
            level['nodes'] = [n for n in level.get('nodes', []) if n['id'] not in ids_to_remove]
            if len(level.get('nodes', [])) < original_count:
                node_found = True

        if not node_found:
            return Response({'error': 'Node not found.'}, status=status.HTTP_404_NOT_FOUND)

        product_structures_col.update_one(
            {'seller_id': request.user.id},
            {'$set': {'levels': levels, 'updated_at': datetime.now(timezone.utc)}}
        )
        return Response(
            {'message': f'Node and {len(ids_to_remove) - 1} descendant(s) deleted.'},
            status=status.HTTP_200_OK
        )


class NodeFieldSchemaView(APIView):
    """
    GET /api/catalog/nodes/<node_id>/fields/  — Get field schema for a node.
    PUT /api/catalog/nodes/<node_id>/fields/  — Set/replace the full field schema for a leaf node.
    """
    permission_classes = [IsAuthenticated]

    def get(self, request, node_id):
        if request.user.role != 'seller':
            return Response({'error': 'Access denied. Sellers only.'}, status=status.HTTP_403_FORBIDDEN)

        doc = _get_structure(request.user.id)
        if not doc:
            return Response({'error': 'Product structure not initialized yet.'}, status=status.HTTP_400_BAD_REQUEST)

        levels = doc.get('levels', [])
        _, node = _find_node_in_levels(levels, node_id)
        if node is None:
            return Response({'error': 'Node not found.'}, status=status.HTTP_404_NOT_FOUND)

        return Response({'node_id': node_id, 'field_schema': node.get('field_schema', [])}, status=status.HTTP_200_OK)

    def put(self, request, node_id):
        """Completely replace the field schema for a node."""
        if request.user.role != 'seller':
            return Response({'error': 'Access denied. Sellers only.'}, status=status.HTTP_403_FORBIDDEN)

        doc = _get_structure(request.user.id)
        if not doc:
            return Response({'error': 'Product structure not initialized yet.'}, status=status.HTTP_400_BAD_REQUEST)

        serializer = SetFieldSchemaSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        levels = doc.get('levels', [])
        node_found = False
        for level in levels:
            for node in level.get('nodes', []):
                if node['id'] == node_id:
                    node['field_schema'] = serializer.validated_data['fields']
                    node_found = True
                    break
            if node_found:
                break

        if not node_found:
            return Response({'error': 'Node not found.'}, status=status.HTTP_404_NOT_FOUND)

        product_structures_col.update_one(
            {'seller_id': request.user.id},
            {'$set': {'levels': levels, 'updated_at': datetime.now(timezone.utc)}}
        )
        return Response({'message': 'Field schema updated successfully.'}, status=status.HTTP_200_OK)


class SaveFullStructureView(APIView):
    """
    POST /api/catalog/structure/save/
    Save the complete product structure in a single payload (used by the wizard's final step).
    """
    permission_classes = [IsAuthenticated]

    def post(self, request):
        if request.user.role != 'seller':
            return Response({'error': 'Access denied. Sellers only.'}, status=status.HTTP_403_FORBIDDEN)

        serializer = ProductStructureSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        data = serializer.validated_data
        now = datetime.now(timezone.utc)

        # Ensure every node has a stable UUID id
        levels = data.get('levels', [])
        for level in levels:
            for node in level.get('nodes', []):
                if not node.get('id'):
                    node['id'] = str(uuid.uuid4())

        doc = {
            'seller_id': request.user.id,
            'top_category': data.get('top_category'),
            'levels': levels,
            'updated_at': now,
        }

        existing = _get_structure(request.user.id)
        if existing:
            doc['created_at'] = existing.get('created_at', now)
        else:
            doc['created_at'] = now

        product_structures_col.replace_one(
            {'seller_id': request.user.id},
            doc,
            upsert=True
        )

        return Response(
            {'message': 'Product structure saved successfully.', 'structure': _serialize_structure(doc)},
            status=status.HTTP_200_OK
        )
