function SumTotalHours() {
    var total = 0;
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
    $(".hour-for-total input").keyup(function() {
        SumTotalHours()
    });
});
