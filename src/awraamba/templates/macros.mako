
<!-- 
  
  Utility functions.
  
  
-->

<%def name="render_item(item)">
  <%
    method_name = item[0]
    args = len(item) > 1 and item[1] or tuple()
    if args and isinstance(args, basestring):
        args = (args,)
    kwargs = len(item) > 2 and item[2] or dict()
  %>
  ${getattr(self, method_name)(*args, **kwargs)}
</%def>

<!-- 
  
  Form template.
  
  
-->

<%def name="form(attrs={}, fields=(), actions=())">
    <%
      attrs_str = ''
      for k, v in attrs.iteritems():
          attrs_str += ' %s="%s"' % (k, v)
    %>
    <form ${attrs_str.strip()}>
      <input type="hidden" name="csrf_token" value="${request.session.get_csrf_token()}" />
      % if message:
        <div class="alert-message error">
          <a class="close" href="#">×</a>
          <p>${_(message)}</p>
        </div>
      % endif
      <fieldset>
        % for item in fields:
          ${self.render_item(item)}
        % endfor
        <div class="actions">
          % for item in actions:
            ${self.render_item(item)}
          % endfor
        </div>
      </fieldset>
    </form>
</%def>

<!-- 
  
  Form inputs.
  
  
-->

<%def name="_input(input_type, name, id=None, value=None, label=None, context_=None)">
  <%
    label = label and label or name.title()
    id = id and id or name
    if value is None:
        value = request.params.get(name, getattr(context_, name, ''))
    is_error = errors and name in errors
    error_class = is_error and 'error' or ''
  %>
  <div class="clearfix ${error_class}">
    <label for="${name}">${_(label)}</label>
    <div class="input">
      <input id="${id}" name="${name}" class="${error_class}" type="${input_type}"
          % if value:
            value="${escape(value)}"
          % endif
      />
      % if is_error:
        <span class="help-inline">${escape(_(errors[name]))}</span>
      % endif
    </div>
  </div>
</%def>

<%def name="text_input(name, id=None, label=None, context_=None)">
  ${self._input('text', name, id=id, label=label, context_=context_)}
</%def>

<%def name="password_input(name, id=None, label=None, context_=None)">
  ${self._input('password', name, id=id, label=label, context_=context_)}
</%def>

<!-- 
  
  Form actions.
  
  
-->

<%def name="_action(input_type, value, is_primary=True)">
  <input type="${input_type}" class="btn ${is_primary and 'primary' or ''}" value="${escape(value)}" />
</%def>

<%def name="submit_action(value, is_primary=True)">
  ${self._action('submit', value, is_primary=is_primary)}
</%def>
