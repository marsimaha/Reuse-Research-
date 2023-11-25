$(document).ready(function() {
    $("form").submit(function(event) {
        event.preventDefault();
        
        let search_query = $("input[name='search_bar']").val();
        let states = {
            'IFC': $('#IFC').prop('checked'),
            'eBKP': $('#eBKP').prop('checked'),
            'MF': $('#MF').prop('checked')
        };

        $.ajax({
            url: '/',
            method: 'POST',
            contentType: 'application/json',
            data: JSON.stringify({ states: states, search_bar: search_query }),
            success: function(response) {
                var result = $('#result')
                $(result).empty()
                $(result).append(response)

                
            },
            error: function(error) {
                console.log("Error:", error);
            }
        });
    });
});
