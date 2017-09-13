// Update generated at time at bottom of pages
(function(){
  try {
    var generated_at = document.getElementById("generated-at");
    var m = moment(generated_at.innerText);
    var update_generated_at = function () {
      generated_at.innerText = "Generated on " + m.format("MMMM Do, YYYY")
        + " at " + m.format("h:mm a") + " (" + m.fromNow() + ")";
    }

    update_generated_at()
    setInterval(update_generated_at, 60*1000);
  } catch ( e ) {
    console.error(e);
  }
})();
