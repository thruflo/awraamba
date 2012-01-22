# ...
define 'views', (exports, root) ->
  
  # `Resizer` binds to throttled window resize events to resize ``@el`` to
  # the viewport dimensions.
  class Resizer extends Backbone.View
    defaults:
      w: 0
      h: 80
    resize: ->
      $target = @$el
      $target.height window.innerHeight - @options.h
      $target.width window.innerWidth - @options.w
    
    initialize: ->
      @options = _.defaults @options, @defaults
      resize = => @resize()
      throttled_resize = _.throttle resize, 250
      $(window).bind 'resize', throttled_resize
    
  
  # Show the intro screen and handle clicks on the enter link by navigating to
  # the request path stored in its model value.
  class IntroView extends Backbone.View
    events:
      'dblclick #intro-enter-link'  : 'next'
      'click #intro-enter-link'     : 'next'
    
    next: ->
      path = @model.get 'value'
      if not path or path.startsWith('/intro')
        path = '/'
      app.navigate path, true
      false
    
    initialize: ->
      $target = $ @el
      $container = $ "#intro-video-container"
      @player = Popcorn "#intro-video"
      # Before hide, pause and rewind the video player and fade the video out.
      # When the fade is done, rewind to the beginning.
      @bind 'beforehide', => 
        @player.pause()
        $container.animate opacity: 0, 750, =>
          @player.currentTime 0
      @bind 'hide', => 
        $target.hide()
      @bind 'show', =>
        $container.css opacity: 0
        $target.show()
      # After show, pause for two seconds, then fade the video in and play
      # from the beginning.
      @bind 'aftershow', =>
        window.setTimeout =>
            $container.animate opacity: 1, 1500, =>
               @player.play 0
          , 2000
    
  
  # Embed and hook up the krpano panorama and switch to the selected scenes when
  # the scene name stored in the model value changes.
  class ExploreView extends Backbone.View
    defaults:
      scene_name: 'village-square'
    
    render: =>
      # Update the panorama location.
      scene_name = @model.get 'value'
      scene_name = @options.scene_name if not scene_name?
      @krpano.call "loadscene('scene_#{scene_name}', null, MERGE);"
    
    initialize: ->
      _.defaults @options, @defaults
      # Resize the container manually.
      resizer = new views.Resizer el: $('#explore-panorama')
      resizer.resize()
      # Hide and show *without* a repaint to keep the panorama state.
      # XXX cross browser testing.
      $target = $ @el
      @bind 'hide', => $target.css visibility: 'hidden'
      @bind 'show', => $target.css visibility: 'visible'
      # Bind once to the krpano "load event".
      root.krpano_loaded = =>
        # Before starting the fade out, we freeze the view.  After the fade out,
        # we re-enable the user interaction.
        @krpano = $('#krpanoSWFObject').get 0
        @bind 'beforehide', => @krpano.call "freezeview(true);" if @krpano.call?
        @bind 'aftershow', => @krpano.call "freezeview(false);" if @krpano.call?
        # Show the initial scene and change scene when the model value changes.
        @model.bind 'change', @render
        @render()
        # Ignore future "events"
        root.krpano_loaded = $.noop
      # Embed the krpano viewer.
      embedpano swf: '/tour/tour.swf', target: 'explore-panorama', xml: '/tour/tour.xml'
    
  
  # Simple container menu -- does nothing.
  class WatchView extends Backbone.View
    render: => # pass
    initialize: ->
      # Show hide using display none.
      $target = $ @el
      @bind 'hide', => $target.hide()
      @bind 'show', => $target.show()
    
  
  # Apply the Popcorn.js viewer to the `<video id="theme-video" /> element and
  # switch video when the selected theme changes.
  class ThemeView extends Backbone.View
    defaults:
      extensions: ['mp4', 'ogv', 'webm']
      videos_path: 'http://videos.mozilla.org/serv/webmademovies/'
    
    render: =>
      theme = @model.get 'value'
      # XXX fake for now using mozilla sources
      theme = if theme is 'gender' then 'thankyou' else 'popcorntest'
      # Set srcs.
      path = @options.videos_path
      exts = @options.extensions
      has_changed = false
      @sources.each (i) -> 
        $source = $ this
        existing_src = $source.attr 'src'
        new_src = "#{path}#{theme}.#{exts[i]}"
        if new_src isnt existing_src
          $source.attr 'src', new_src
          has_changed = true
      if has_changed
        @player.load()
      @player.play()
    
    initialize: ->
      _.defaults @options, @defaults
      # Show hide using display none.
      $target = $ @el
      @bind 'hide', => $target.hide()
      @bind 'show', => $target.show()
      # Initialise Popcorn.js player.
      @player = Popcorn "#theme-video"
      @player.media.autoplay = true
      # Get a handle on the <source /> elements.
      @sources = @$ '#theme-video > source'
      # Pause and play on before hide and after show.
      @bind 'beforehide', => @player.pause()
      @bind 'aftershow', => @player.play()
      # Bind to theme changes and render.
      @model.bind 'change', @render
      @render()
    
  
  # ...
  class InteractView extends Backbone.View
    render: ->
      # ...
    
    initialize: ->
      @model.bind 'change', @render
      $target = $ @el
      @bind 'afterhide', => $target.hide()
      @bind 'beforeshow', => $target.show()
    
  
  exports.Resizer = Resizer
  exports.IntroView = IntroView
  exports.ExploreView = ExploreView
  exports.WatchView = WatchView
  exports.ThemeView = ThemeView
  exports.InteractView = InteractView

