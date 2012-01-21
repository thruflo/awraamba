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
  exports.ExploreView = ExploreView
  exports.WatchView = WatchView
  exports.InteractView = InteractView

