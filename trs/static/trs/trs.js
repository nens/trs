function SumTotalHours() {
    var total = 0;
    var value;
    $('.hour-for-total').each(function() {
        if ($(this).children().length > 0 ) {
            // I have children (= an input element).
            value = $('input', this).val();
        } else {
            // I am not editable, I only have my hours as text.
            value = $(this).text();
        }
        if (!isNaN(value) && (value.length != 0))  {
            total += parseInt(value);
        }
    });
    $('#hour-total').text(total);
}

$(document).ready(function () {
    window.form_changed = false;
    $(".hour-for-total input").keyup(function() {
        SumTotalHours();
        window.form_changed = true;
    });
    window.onbeforeunload = function(e) {
        if (window.form_changed) {
            return "Er is wat veranderd. Klik misschien eerst op submit of enter?";
        }
    };
    $("#booking-form").submit(function(e) {
        window.form_changed = false;
    });
});
