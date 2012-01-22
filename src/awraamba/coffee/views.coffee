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
    render: ->
      # update the panorama location
    
    initialize: ->
      $target = $ '#explore-panorama'
      # Resize the container manually.
      resizer = new views.Resizer el: $target
      resizer.resize()
      # Embed the krpano viewer.
      @viewer = createPanoViewer
        swf: '/tour/tour.swf'
        target: 'explore-panorama'
      @viewer.addVariable "xml", "/tour/tour.xml"
      @viewer.embed()
      # Bind to change events.
      @model.bind 'change', @render
      # Hide and show *without* a repaint to keep the panorama state.
      # XXX cross browser testing.
      $target = $ @el
      krpano = $('#krpanoSWFObject').get 0
      # 1. Before starting the fade out, we freeze the view.
      @bind 'beforehide', => krpano.call "freezeview(true);" if krpano.call?
      # 2. On hide, we set the (already position absoute) container to hidden.
      @bind 'hide', => $target.css visibility: 'hidden'
      # 3. On show, we make it visible again.
      @bind 'show', => $target.css visibility: 'visible'
      # 4. After the fade out, we re-enable the user interaction.
      @bind 'aftershow', => krpano.call "freezeview(false);" if krpano.call?
    
  
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

