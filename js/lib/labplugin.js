var plugin = require('./index');
var base = require('@jupyter-widgets/base');

module.exports = {
  id: 'ipyexperimenter',
  requires: [base.IJupyterWidgetRegistry],
  activate: function(app, widgets) {
      widgets.registerWidget({
          name: 'ipyexperimenter',
          version: plugin.version,
          exports: plugin
      });
  },
  autoStart: true
};

