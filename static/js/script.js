// Custom JavaScript for Library Management System

// Document ready function
$(document).ready(function() {
    // Initialize tooltips
    var tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
    var tooltipList = tooltipTriggerList.map(function (tooltipTriggerEl) {
        return new bootstrap.Tooltip(tooltipTriggerEl);
    });

    // Auto-hide flash messages after 5 seconds
    setTimeout(function() {
        $('.alert').fadeOut('slow');
    }, 5000);

    // Search functionality
    initializeSearch();
    
    // Form validation
    initializeFormValidation();
    
    // Confirmation dialogs
    initializeConfirmDialogs();
    
    // Date pickers
    initializeDatePickers();
});

// Search functionality
function initializeSearch() {
    // Book search
    $('#bookSearch').on('input', function() {
        var query = $(this).val();
        var searchResults = $('#bookSearchResults');
        
        if (query.length < 2) {
            searchResults.hide();
            return;
        }
        
        $.ajax({
            url: '/books/search',
            method: 'GET',
            data: { q: query },
            success: function(data) {
                searchResults.empty();
                
                if (data.length === 0) {
                    searchResults.html('<div class="search-result-item">No books found</div>');
                } else {
                    data.forEach(function(book) {
                        var availability = book.available ? 
                            '<span class="badge bg-success">Available</span>' : 
                            '<span class="badge bg-danger">Unavailable</span>';
                        
                        searchResults.append(
                            '<div class="search-result-item" onclick="selectBook(' + book.id + ', \'' + book.title + '\')">' +
                            '<strong>' + book.title + '</strong> by ' + book.author + ' ' + availability +
                            '</div>'
                        );
                    });
                }
                
                searchResults.show();
            },
            error: function() {
                searchResults.html('<div class="search-result-item">Error searching books</div>');
                searchResults.show();
            }
        });
    });
    
    // User search (admin only)
    $('#userSearch').on('input', function() {
        var query = $(this).val();
        var searchResults = $('#userSearchResults');
        
        if (query.length < 2) {
            searchResults.hide();
            return;
        }
        
        $.ajax({
            url: '/transactions/search_users',
            method: 'GET',
            data: { q: query },
            success: function(data) {
                searchResults.empty();
                
                if (data.length === 0) {
                    searchResults.html('<div class="search-result-item">No users found</div>');
                } else {
                    data.forEach(function(user) {
                        var userType = user.user_type === 'admin' ? 
                            '<span class="badge bg-primary">Admin</span>' : 
                            '<span class="badge bg-info">Student</span>';
                        
                        searchResults.append(
                            '<div class="search-result-item" onclick="selectUser(' + user.id + ', \'' + user.full_name + '\')">' +
                            '<strong>' + user.full_name + '</strong> (' + user.username + ') ' + userType +
                            '</div>'
                        );
                    });
                }
                
                searchResults.show();
            },
            error: function() {
                searchResults.html('<div class="search-result-item">Error searching users</div>');
                searchResults.show();
            }
        });
    });
    
    // Hide search results when clicking outside
    $(document).on('click', function(e) {
        if (!$(e.target).closest('.search-box').length) {
            $('.search-results').hide();
        }
    });
}

// Select book from search results
function selectBook(bookId, bookTitle) {
    $('#book_id').val(bookId);
    $('#bookSearch').val(bookTitle);
    $('#bookSearchResults').hide();
}

// Select user from search results
function selectUser(userId, userName) {
    $('#user_id').val(userId);
    $('#userSearch').val(userName);
    $('#userSearchResults').hide();
}

// Form validation
function initializeFormValidation() {
    // Add custom validation rules
    $.validator.addMethod('isbn', function(value) {
        // Basic ISBN validation (10 or 13 digits, with or without hyphens)
        return /^[0-9-]{10,17}$/.test(value);
    }, 'Please enter a valid ISBN');
    
    // Validate forms with data-validate attribute
    $('form[data-validate]').each(function() {
        $(this).validate({
            errorClass: 'is-invalid',
            errorElement: 'div',
            highlight: function(element) {
                $(element).addClass('is-invalid').removeClass('is-valid');
            },
            unhighlight: function(element) {
                $(element).removeClass('is-invalid').addClass('is-valid');
            },
            errorPlacement: function(error, element) {
                error.insertAfter(element);
            }
        });
    });
}

// Confirmation dialogs
function initializeConfirmDialogs() {
    // Delete confirmation
    $('.delete-btn').on('click', function(e) {
        e.preventDefault();
        var form = $(this).closest('form');
        var itemName = $(this).data('item-name') || 'this item';
        
        if (confirm('Are you sure you want to delete ' + itemName + '? This action cannot be undone.')) {
            form.submit();
        }
    });
    
    // Return book confirmation
    $('.return-btn').on('click', function(e) {
        e.preventDefault();
        var form = $(this).closest('form');
        var bookTitle = $(this).data('book-title') || 'this book';
        
        if (confirm('Are you sure you want to return "' + bookTitle + '"?')) {
            form.submit();
        }
    });
}

// Date pickers
function initializeDatePickers() {
    // Initialize date pickers for date inputs
    $('input[type="date"]').each(function() {
        // Set default date if not specified
        if (!$(this).val()) {
            var today = new Date().toISOString().split('T')[0];
            $(this).attr('min', today);
        }
    });
    
    // Due date calculator
    $('#due_days').on('input', function() {
        var days = parseInt($(this).val()) || 14;
        var dueDate = new Date();
        dueDate.setDate(dueDate.getDate() + days);
        
        $('#due_date_display').text(dueDate.toLocaleDateString());
    });
}

// Utility functions
function formatDate(dateString) {
    var date = new Date(dateString);
    return date.toLocaleDateString() + ' ' + date.toLocaleTimeString();
}

function formatCurrency(amount) {
    return new Intl.NumberFormat('en-US', {
        style: 'currency',
        currency: 'USD'
    }).format(amount);
}

// AJAX functions
function ajaxRequest(url, method, data, successCallback, errorCallback) {
    $.ajax({
        url: url,
        method: method,
        data: data,
        success: successCallback,
        error: errorCallback || function(xhr, status, error) {
            console.error('AJAX Error:', error);
            alert('An error occurred. Please try again.');
        }
    });
}

// Loading indicator
function showLoading(element) {
    $(element).html('<div class="spinner"></div> Loading...');
}

function hideLoading(element, originalContent) {
    $(element).html(originalContent);
}

// Print functionality
function printReport(reportId) {
    var printContents = document.getElementById(reportId).innerHTML;
    var originalContents = document.body.innerHTML;
    
    document.body.innerHTML = printContents;
    window.print();
    document.body.innerHTML = originalContents;
    
    // Reinitialize JavaScript after print
    location.reload();
}

// Export functionality
function exportReport(reportType) {
    window.open('/reports/export/' + reportType, '_blank');
}

// Real-time updates (if implemented with WebSockets)
function initializeRealTimeUpdates() {
    // This would be used for real-time notifications
    // Implementation depends on WebSocket library used
}

// Keyboard shortcuts
$(document).on('keydown', function(e) {
    // Ctrl+K for search
    if (e.ctrlKey && e.key === 'k') {
        e.preventDefault();
        $('#bookSearch, #userSearch').first().focus();
    }
    
    // Escape to close modals
    if (e.key === 'Escape') {
        $('.modal').modal('hide');
        $('.search-results').hide();
    }
});

// Auto-refresh for dashboard (optional)
function startAutoRefresh() {
    setInterval(function() {
        // Only refresh if user is on dashboard
        if (window.location.pathname === '/' || window.location.pathname === '/dashboard') {
            location.reload();
        }
    }, 300000); // Refresh every 5 minutes
}

// Initialize auto-refresh on dashboard
if (window.location.pathname === '/' || window.location.pathname === '/dashboard') {
    // startAutoRefresh(); // Uncomment if auto-refresh is desired
}

// Chart initialization (if charts are used)
function initializeCharts() {
    // This would be used to initialize charts for reports
    // Implementation depends on charting library used (Chart.js, etc.)
}

// Responsive table handling
function handleResponsiveTables() {
    $('.table-responsive').each(function() {
        var table = $(this).find('table');
        var headers = [];
        
        // Get headers
        table.find('thead th').each(function() {
            headers.push($(this).text());
        });
        
        // Add data attributes to cells for mobile view
        table.find('tbody tr').each(function() {
            $(this).find('td').each(function(index) {
                $(this).attr('data-label', headers[index]);
            });
        });
    });
}

// Initialize responsive tables
handleResponsiveTables();
