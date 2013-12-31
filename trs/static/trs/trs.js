function SumTotalHours() {
    var total = 0;
    $('.hour-for-total input').each(function() {
        value = $(this).val();
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
