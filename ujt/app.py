# Copyright 2020 Chuan Chen

# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at

#    http://www.apache.org/licenses/LICENSE-2.0

# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
""" Main module for Dash app. """

import dash
import dash_cytoscape as cyto
import dash_html_components as html

app = dash.Dash(__name__)

app.layout = html.Div([
    cyto.Cytoscape(id='cytoscape-two-nodes',
                   layout={'name': 'preset'},
                   style={
                       'width': '100%',
                       'height': '400px'
                   },
                   elements=[{
                       'data': {
                           'id': 'one',
                           'label': 'Node 1'
                       },
                       'position': {
                           'x': 75,
                           'y': 75
                       }
                   }, {
                       'data': {
                           'id': 'two',
                           'label': 'Node 2'
                       },
                       'position': {
                           'x': 200,
                           'y': 200
                       }
                   }, {
                       'data': {
                           'source': 'one',
                           'target': 'two'
                       }
                   }])
])

if __name__ == '__main__':
    app.run_server(debug=True)
