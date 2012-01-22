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
    
  
  # Show the intro screen and handle clicks by navigating to 
  # `"/#{@model.get 'value'}"`.
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
    
  
  # ...
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
    
  
  # ...
  class WatchView extends Backbone.View
    render: ->
      # ...
    
    initialize: ->
      @model.bind 'change', @render
      $target = $ @el
      @bind 'afterhide', => $target.hide()
      @bind 'beforeshow', => $target.show()
    
  
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
  exports.InteractView = InteractView

