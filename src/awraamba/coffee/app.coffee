underscore = _.noConflict()

handle_resize = ->
  h = window.innerHeight - 160
  w = window.innerWidth - 40
  $target = $ '#main-content'
  $target.height '' + h + 'px'
  $target.width '' + w + 'px'

throttled_resize = underscore.throttle handle_resize, 250

$window = $ window
$window.bind 'resize', throttled_resize

$document = $ document
$document.ready ->
  handle_resize()
  viewer = createPanoViewer
    swf: '/tour/tour.swf'
    target: 'explore-panorama'
  viewer.addVariable "xml", "/tour/tour.xml"
  viewer.embed()

