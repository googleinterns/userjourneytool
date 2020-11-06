""" Module holding constants for Dash components.

Let's improve the naming convention.
For signals, it makes sense to me to place the type first (i.e. "SIGNAL_*"),
since we want to quickly identify that it's a signal and we often group signals together.

For other types of components, it's unclear if this is better.
For instance, with panels, it's good to be able to quickly see that the component is a panel,
which tells us that the callback should probably return a group of components.
However, with buttons or other components, it might be more useful to see 
the type of action that the component is associated with first.

It also seems more natural/readable in most instances to place the component type last. 
It's a bit unwieldly to use the component type first convention
if we have only a single component of a single type (e.g. ModalHeader, etc).

For now, signals use the component type first convention, and all other
component ids place the component type at the end.
"""


# region signals
SIGNAL_VIRTUAL_NODE_UPDATE = "virtual-node-update-signal"

SIGNAL_TAG_CREATE = "create-tag-signal"
SIGNAL_TAG_DELETE = "delete-tag-signal"
SIGNAL_TAG_SAVE = "save-tag-signal"
SIGNAL_TAG_UPDATE = "tag-update-signal"

SIGNAL_APPLIED_TAG_ADD = "add-applied-tag-signal"
SIGNAL_APPLIED_TAG_REMOVE = "remove-applied-tag-signal"
SIGNAL_APPLIED_TAG_MODIFY = "modify-applied-tag-signal"
SIGNAL_APPLIED_TAG_BATCH_ADD = "batch-add-applied-tag-signal"
SIGNAL_APPLIED_TAG_BATCH_REMOVE = "batch-remove-applied-tag-signal"
SIGNAL_APPLIED_TAG_UPDATE = "applied-tag-update-signal"

SIGNAL_VIEW_UPDATE = "view-update-signal"

SIGNAL_STYLE_SAVE = "save-style-signal"
SIGNAL_STYLE_DELETE = "delete-style-signal"
SIGNAL_STYLE_UPDATE = "style-update-signal"

SIGNAL_COMPOSITE_TAGGING_UPDATE = "composite-tagging-update-signal"
# ---
SIGNAL_WRAPPER_DIV = "signal-wrapper-div"
# endregion

# region error modal (virtual nodes)
COLLAPSE_ERROR_MODAL = "collapse-error-modal"
COLLAPSE_ERROR_MODAL_BODY = "collapse-error-modal-body"
COLLAPSE_ERROR_MODAL_CLOSE = "collapse-error-modal-close"
# endregion

# region top bar
REFRESH_SLI_BUTTON = "refresh-sli-button"

VIRTUAL_NODE_INPUT = "virtual-node-input"
ADD_VIRTUAL_NODE_BUTTON = "add-virtual-node-button"
DELETE_VIRTUAL_NODE_BUTTON = "delete-virtual-node-button"
COLLAPSE_VIRTUAL_NODE_BUTTON = "collapse-virtual-node-button"
EXPAND_VIRTUAL_NODE_BUTTON = "expand-virtual-node-button"

BATCH_APPLIED_TAG_DROPDOWN = "batch-applied-tag-dropdown"
BATCH_ADD_APPLIED_TAG_BUTTON = "batch-add-applied-tag-button"
BATCH_REMOVE_APPLIED_TAG_BUTTON = "batch-remove-applied-tag-button"
# endregion

CYTOSCAPE_GRAPH = "cytoscape-graph"

# region bottom panels
CREATE_TAG_PANEL = "create-tag-panel"
VIEW_PANEL = "view-panel"
STYLE_PANEL = "style-panel"

SELECTED_INFO_PANEL = "selected-info-panel"
USER_JOURNEY_DROPDOWN = "user-journey-dropdown"
USER_JOURNEY_INFO_PANEL = "user-journey-info-panel"
# endregion

# region selected info panel
OVERRIDE_DROPDOWN = "override-dropdown"
OVERRIDE_DROPDOWN_HIDDEN = "override-dropdown-hidden"
SLI_DATATABLE = "datatable-slis"
CHILD_DATATABLE = "datatable-child-nodes"
DEPENDENCY_DATATABLE = "datatable-dependency-nodes"
# endregion

# region user journey panel
# this isn't accessed in components.py -- dynamically generated from and used in callbacks.py
USER_JOURNEY_DATATABLE = "user-journey-datatable"
# endregion

# region comments
NODE_COMMENT_TEXTAREA = "node-comment-textarea"
SAVE_COMMENT_TEXTAREA_BUTTON = "save-comment-textarea-button"
DISCARD_COMMENT_TEXTAREA_BUTTON = "discard-comment-textarea-button"
SAVE_COMMENT_TOAST = "save-comment-toast"
# endregion

# region apply tag
APPLIED_TAG_DROPDOWN = "applied-tag-dropdown"
REMOVE_APPLIED_TAG_BUTTON = "remove-applied-tag-button"
ADD_APPLIED_TAG_BUTTON = "add-applied-tag-button"
# endregion

# region create tag
TAG_INPUT = "tag-input"
DELETE_TAG_BUTTON = "delete-tag-button"
SAVE_TAG_BUTTON = "save-tag-button"
CREATE_TAG_BUTTON = "create-tag-button"
SAVE_TAG_TOAST = "save-tag-toast"
# endregion

# region views
VIEW_TAG_DROPDOWN = "view-tag-dropdown"
VIEW_STYLE_DROPDOWN = "view-style-dropdown"
DELETE_VIEW_BUTTON = "delete-view-button"
CREATE_VIEW_BUTTON = "create-view-button"
VIEW_STORE = "view-store"
# endregion

# region style
STYLE_NAME_INPUT = "style-name-input"
STYLE_TEXTAREA = "style-textarea"
LOAD_STYLE_TEXTAREA_BUTTON = "load-style-textarea-button"
SAVE_STYLE_TEXTAREA_BUTTON = "save-style-textarea-button"
DELETE_STYLE_BUTTON = "delete-style-button"
SAVE_STYLE_TOAST = "save-style-toast"
# endregion

# region cache keys
NODE_NAME_MESSAGE_MAP = "node_name_message_map"
CLIENT_NAME_MESSAGE_MAP = "client_name_message_map"

VIRTUAL_NODE_MAP = "virtual_node_map"
PARENT_VIRTUAL_NODE_MAP = "parent_virtual_node_map"
COMMENT_MAP = "comment_map"
OVERRIDE_STATUS_MAP = "override_status_map"
TAG_LIST = "tag_list"
TAG_MAP = "tag_map"
STYLE_MAP = "style_map"
VIEW_LIST = "view_list"
# endregion

# region change over time
CHANGE_OVER_TIME_PANEL = "change-over-time-panel"
CHANGE_OVER_TIME_SLI_TYPE_DROPDOWN = "change-over-time-sli-type-dropdown"
CHANGE_OVER_TIME_TAG_DROPDOWN = "change-over-time-tag-dropdown"
TIME_SELECT_PANEL = "time-select-panel"
CHANGE_OVER_TIME_QUERY_BUTTON = "change-over-time-query-button"
CHANGE_OVER_TIME_RESET_BUTTON = "change-over-time-reset-button"
CHANGE_OVER_TIME_ERROR_TOAST = "change-over-time-error-toast"

START_TIME_INPUT = "start-time-input"
END_TIME_INPUT = "end-time-input"
WINDOW_SIZE_INPUT = "window-size-input"
CHANGE_OVER_TIME_SLI_STORE = "change-over-time-sli-store"

CHANGE_OVER_TIME_TEXT_OUTPUT_PANEL = "change-over-time-text-output-panel"
CHANGE_OVER_TIME_DATATABLE = "change-over-time-datatable"
# endregion
