
<!DOCTYPE html>
<html>
<head>
  <title>Nietzsche Ipsum</title>
  <link href="style.css" rel="stylesheet">
  <script src="jquery.js"></script>
  <script src="ipsum.js"></script>
  <meta name="viewport" content="initial-scale=1, maximum-scale=1">
</head>
<body>

  <!-- Facebook -->
  <div id="fb-root"></div>
  <script>(function(d, s, id) {
    var js, fjs = d.getElementsByTagName(s)[0];
    if (d.getElementById(id)) return;
    js = d.createElement(s); js.id = id;
    js.src = "https://connect.facebook.net/en_US/all.js#xfbml=1&appId=1382251568663988";
    fjs.parentNode.insertBefore(js, fjs);
  }(document, 'script', 'facebook-jssdk'));</script>

  <!-- Actual code -->
  <div class="container">

    <header>
      <img src="nietzsche.jpg">
      <h1>Nietzsche Ipsum</h1>
      <p>I desire <input type="number" id="num" value="150"> words of truth</p>
      <p><button id="generate">Ecce Ipsum</button></p>
    </header>

    <div class="social-share">
      <a href="https://twitter.com/share" class="twitter-share-button" data-via="nbashaw" data-size="small" data-related="nbashaw">Tweet</a>
      <div class="fb-like" data-href="http://nietzsche-ipsum.ga.co/" data-layout="button_count" data-action="like" data-show-faces="true" data-share="true"></div>
    </div>

    <div class="ipsum-container"></div>

    <a class="footer" href="https://twitter.com/nbashaw" target="_blank">
      Made with &hearts; by <span class="ga">@nbashaw</span>
    </a>

  </div>

  <!-- Social -->
  <script>!function(d,s,id){var js,fjs=d.getElementsByTagName(s)[0],p=/^http:/.test(d.location)?'http':'https';if(!d.getElementById(id)){js=d.createElement(s);js.id=id;js.src=p+'://platform.twitter.com/widgets.js';fjs.parentNode.insertBefore(js,fjs);}}(document, 'script', 'twitter-wjs');</script>

  <script>
    (function(i,s,o,g,r,a,m){i['GoogleAnalyticsObject']=r;i[r]=i[r]||function(){
    (i[r].q=i[r].q||[]).push(arguments)},i[r].l=1*new Date();a=s.createElement(o),
    m=s.getElementsByTagName(o)[0];a.async=1;a.src=g;m.parentNode.insertBefore(a,m)
    })(window,document,'script','//www.google-analytics.com/analytics.js','ga');

    ga('create', 'UA-60155752-1', 'auto');
    ga('send', 'pageview');

  </script>

</body>
</html>
