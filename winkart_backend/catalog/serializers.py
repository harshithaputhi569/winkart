from rest_framework import serializers


class FieldSchemaSerializer(serializers.Serializer):
    """A single field definition attached to a leaf node."""
    label = serializers.CharField(max_length=100)
    field_type = serializers.ChoiceField(
        choices=['text', 'number', 'dropdown', 'boolean', 'unit']
    )
    unit = serializers.CharField(max_length=30, allow_blank=True, required=False, default='')
    options = serializers.ListField(
        child=serializers.CharField(max_length=100),
        required=False,
        default=list
    )
    required = serializers.BooleanField(default=False)


class NodeSerializer(serializers.Serializer):
    """A single category node in the tree."""
    id = serializers.CharField(max_length=64)
    name = serializers.CharField(max_length=150)
    parent_id = serializers.CharField(max_length=64, allow_null=True, required=False, default=None)
    field_schema = FieldSchemaSerializer(many=True, required=False, default=list)


class LevelSerializer(serializers.Serializer):
    """A single depth-level in the category hierarchy."""
    level_index = serializers.IntegerField(min_value=0)
    level_name = serializers.CharField(max_length=100)
    nodes = NodeSerializer(many=True, required=False, default=list)


class TopCategorySerializer(serializers.Serializer):
    """The root / top-level category for the seller's product structure."""
    name = serializers.CharField(max_length=150)
    icon = serializers.CharField(max_length=60, allow_blank=True, required=False, default='grid-outline')
    is_preset = serializers.BooleanField(default=False)


class ProductStructureSerializer(serializers.Serializer):
    """Full product structure document."""
    top_category = TopCategorySerializer(required=False)
    levels = LevelSerializer(many=True, required=False, default=list)


# ── Operational Serializers (for individual PATCH/ADD operations) ──────────

class AddNodeSerializer(serializers.Serializer):
    """Payload to add a new node under an existing level."""
    level_index = serializers.IntegerField(min_value=0)
    name = serializers.CharField(max_length=150)
    parent_id = serializers.CharField(max_length=64, allow_null=True, required=False, default=None)


class RenameNodeSerializer(serializers.Serializer):
    """Payload to rename a node."""
    name = serializers.CharField(max_length=150)


class UpdateLevelNameSerializer(serializers.Serializer):
    """Payload to rename a hierarchy level."""
    level_index = serializers.IntegerField(min_value=0)
    level_name = serializers.CharField(max_length=100)


class AddLevelSerializer(serializers.Serializer):
    """Payload to add a new depth level."""
    level_name = serializers.CharField(max_length=100)


class SetFieldSchemaSerializer(serializers.Serializer):
    """Payload to set the field schema for a leaf node."""
    fields = FieldSchemaSerializer(many=True)
