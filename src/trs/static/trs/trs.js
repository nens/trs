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


function SumColumnHours(column) {
    // Column is like "col1"
    var total = 0;
    var value;
    var cls = ".hour-for-" + column;
    var total_id = "#hour-total-" + column;
    $(cls).each(function() {
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
    $(total_id).text(total);
}


function configureSelectionPager() {
    var selection_pager = JSON.parse(localStorage.getItem('selection_pager'));
    var selection_pager_start_url = localStorage.getItem(
        'selection_pager_start_url');

    if (selection_pager) {
        $("#selection-pager").show();
        $("#disable-selection-pager").show();
    }
    if (for_selection_pager) {
        // for_selection_pager is defined in base.html for pagers where there
        // is such a list available for the selection pager.
        if (selection_pager) {
            $("#enable-selection-pager-refresh").show();
        } else {
            $("#enable-selection-pager").show();
        }
    }

    $("#enable-selection-pager a, #enable-selection-pager-refresh a").click(
        function(e) {
            e.preventDefault();
            localStorage.setItem('selection_pager',
                                 JSON.stringify(for_selection_pager));
            localStorage.setItem('selection_pager_start_url',
                                 document.location.href);
            document.location.reload();
        });
    $("#disable-selection-pager a").click(function(e) {
        e.preventDefault();
        localStorage.removeItem('selection_pager');
        document.location.href = selection_pager_start_url;
    });
    if (selection_pager) {
        var selection_pager_contents = '';
        var selection_pager_next;
        $.each(selection_pager, function(index, item) {
            base_url = item.url.split('?')[0];
            if (window.location.pathname == base_url) {
                // This is the selected item.
                extra = ' class="selected" ';
                if (selection_pager[index + 1]) {
                    selection_pager_next = selection_pager[index + 1].url;
                }
            } else {
                extra = '';
            }
            selection_pager_contents += (
                '<li><a href="' +
                    item.url +
                    '"' +
                    extra +
                    '>' +
                    item.name +
                    '</a></li>');
        });
        $('#selection-pager-contents').html(selection_pager_contents);
        if (selection_pager_next) {
            $("#selection-pager-next").show();
            $("#selection-pager-next a").attr('href', selection_pager_next);
        }
    }
}


$(document).ready(function () {
    // We sum the totals right at the beginning also. Handier at the moment than passing
    // it along in the form. We should create a more generic mechanism for this. (Or
    // refactor the form once the week/date change is complete).
    SumColumnHours("col1");
    SumColumnHours("col2");
    SumColumnHours("col3");
    SumColumnHours("col4");
    SumColumnHours("col5");
    window.form_changed = false;
    $(".hour-for-total input").on("input", function() {
        SumTotalHours();
        SumColumnHours("col1");
        SumColumnHours("col2");
        SumColumnHours("col3");
        SumColumnHours("col4");
        SumColumnHours("col5");
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
