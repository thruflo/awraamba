# Javascript templates.
define 'templates', (exports, root) ->
  
  exports.thread_content = mobone.string.template """
    <div class="theme-<%- theme_slug %>">
      <a href="/scarf/<%- id %>" class="thread"><span><span></span></span></a>
      <div class="reaction-info">
        <p>
          <span class="by-user">
            <%= i18n._('By') %> 
            @<a href="/users/<%= user_username %>"><%= user_username %></a>
          </span>
          <span class="by-user">
            <% if (typeof(parent_id) != "undefined" && parent_id) { %>
              <%= i18n._('in response to') %> 
              @<a href="/scarf/<%= parent_id %>"><%= parent_user_username %></a>
            <% } %>
            <%= i18n._('reacting to') %>
            <a href="/themes/<%- encodeURIComponent(theme_slug) %>/<%- encodeURIComponent(timecode) %>">
              <%= theme_slug %>#<%= timecode.toMMSS() %></a>.
          </span>
        </p>
        <% if (typeof(url) != "undefined" && url) { %>
          <p class="reaction-url">
            <a href="<%- encodeURI(url) %>"
                rel="external" target="_blank">
              <%= url %>
            </a>
          </p>
        <% } %>
        <% if (typeof(message) != "undefined" && message) { %>
          <p class="reaction-message">
            <%= message %>
          </p>
        <% } %>
      </div>
    </div>
  """

