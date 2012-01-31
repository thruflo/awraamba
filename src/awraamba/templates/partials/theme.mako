<%namespace name="macros" file="../macros.mako"/>
<div id="theme-view" class="relative-view">
  <div id="theme-video-container">
    <video id="theme-video">
      <source></source>
      <source></source>
    </video>
    <div id="watch-react-btns-container">
      <a href="react" id="react-btn" class="btn">${_(u'React')} &raquo;</a>
      <a href="watch" id="watch-btn" class="btn">&laquo; ${_(u'Watch')}</a>
    </div>
  </div>
  <div id="react-ui">
    <h2>${_(u'React')}</h2>
    ${macros.form(
        attrs = dict(action='/api/reactions/', method='post', id='react-form'),
        fields = (
            ('hidden_input', 'theme_id'),
            ('text_input', 'timecode'),
            ('text_input', 'url'),
            ('textarea', 'message'),
        ),
        actions = (
            ('submit_action', _(u'React')),
        )
    )}
  </div>
  <div id="threads-ui" class="threads-ui">
    <ul id="thread-listings" class="threads-listing">
    </ul>
  </div>
</div>
