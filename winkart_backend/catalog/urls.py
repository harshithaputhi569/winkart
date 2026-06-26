from django.urls import path
from catalog.views import (
    ProductStructureView,
    LevelView,
    NodeView,
    NodeFieldSchemaView,
    SaveFullStructureView,
)

urlpatterns = [
    # Full structure — get, init, delete
    path('structure/', ProductStructureView.as_view(), name='catalog-structure'),

    # Bulk save (final step of wizard)
    path('structure/save/', SaveFullStructureView.as_view(), name='catalog-structure-save'),

    # Level management
    path('levels/', LevelView.as_view(), name='catalog-level-add'),
    path('levels/<int:level_index>/', LevelView.as_view(), name='catalog-level-detail'),

    # Node management
    path('nodes/', NodeView.as_view(), name='catalog-node-add'),
    path('nodes/<str:node_id>/', NodeView.as_view(), name='catalog-node-detail'),

    # Field schema for a specific node
    path('nodes/<str:node_id>/fields/', NodeFieldSchemaView.as_view(), name='catalog-node-fields'),
]
