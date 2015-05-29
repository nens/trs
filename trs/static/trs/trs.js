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
        if (!isNaN(value) && (value.length !== 0))  {
            total += parseInt(value, 10);
        }
    });
    $('#hour-total').text(total);
}


function configureSelectionPager() {
    var selection_pager = JSON.parse(localStorage.getItem('selection_pager'));
    var selection_pager_start_url = localStorage.getItem(
        'selection_pager_start_url');

    if (for_selection_pager) {
        // for_selection_pager is defined in base.html for pagers where there
        // is such a list available for the selection pager.
        $("#selection-pager").show();
        $("#enable-selection-pager").show();
    }
    if (selection_pager) {
        $("#selection-pager").show();
        $("#disable-selection-pager").show();
    }

    $("#enable-selection-pager a").click(function(e) {
        localStorage.setItem('selection_pager',
                             JSON.stringify(for_selection_pager));
        localStorage.setItem('selection_pager_start_url',
                             document.location.href);
        document.location.reload();
    });
    $("#disable-selection-pager a").click(function(e) {
        localStorage.removeItem('selection_pager');
        document.location.href = selection_pager_start_url;
    });
    if (selection_pager) {
        var selection_pager_contents = '';
        $.each(selection_pager, function(index, item) {
            if (window.location.pathname == item['url']) {
                extra = ' class="selected" ';
            } else {
                extra = '';
            }
            selection_pager_contents += (
                '<li><a href="' +
                    item['url'] +
                    '"' +
                    extra +
                    '>' +
                    item['name'] +
                    '</a></li>')
        });
        console.log(selection_pager_contents);
        $('#selection-pager-contents').html(selection_pager_contents);
    }
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
    $('.table-fixed-header').fixedHeader();
    configureSelectionPager();
});
