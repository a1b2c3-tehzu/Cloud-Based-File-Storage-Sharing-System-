// Main JavaScript for Cloud Storage System

document.addEventListener('DOMContentLoaded', function() {
    // Initialize theme
    initializeTheme();
    
    // Initialize tooltips
    var tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
    var tooltipList = tooltipTriggerList.map(function (tooltipTriggerEl) {
        return new bootstrap.Tooltip(tooltipTriggerEl);
    });

    // Drag and Drop functionality
    const dropZone = document.getElementById('dropZone');
    const fileInputDrag = document.getElementById('file');
    
    if (dropZone && fileInputDrag) {
        // Prevent default drag behaviors
        ['dragenter', 'dragover', 'dragleave', 'drop'].forEach(eventName => {
            dropZone.addEventListener(eventName, preventDefaults, false);
            document.body.addEventListener(eventName, preventDefaults, false);
        });

        // Highlight drop zone when item is dragged over it
        ['dragenter', 'dragover'].forEach(eventName => {
            dropZone.addEventListener(eventName, highlight, false);
        });

        ['dragleave', 'drop'].forEach(eventName => {
            dropZone.addEventListener(eventName, unhighlight, false);
        });

        // Handle dropped files
        dropZone.addEventListener('drop', handleDrop, false);

        // Handle click to browse
        dropZone.addEventListener('click', () => fileInputDrag.click());
    }

    function preventDefaults(e) {
        e.preventDefault();
        e.stopPropagation();
    }

    function highlight(e) {
        dropZone.classList.add('border-primary', 'bg-light');
    }

    function unhighlight(e) {
        dropZone.classList.remove('border-primary', 'bg-light');
    }

    function handleDrop(e) {
        const dt = e.dataTransfer;
        const files = dt.files;
        
        // Create a new DataTransfer object to properly set files
        const dataTransfer = new DataTransfer();
        for (let i = 0; i < files.length; i++) {
            dataTransfer.items.add(files[i]);
        }
        fileInputDrag.files = dataTransfer.files;
        
        // Manually trigger the change event to update the file input
        const event = new Event('change', { bubbles: true });
        fileInputDrag.dispatchEvent(event);
        
        handleFiles(files);
    }

    // Auto-hide flash messages after 5 seconds
    setTimeout(function() {
        const alerts = document.querySelectorAll('.alert');
        alerts.forEach(function(alert) {
            const bsAlert = new bootstrap.Alert(alert);
            bsAlert.close();
        });
    }, 5000);

    // Enhanced file handling
    function handleFiles(files) {
        if (files.length > 0) {
            const file = files[0];
            displayFilePreview(file);
            validateFile(file);
        }
    }

    function displayFilePreview(file) {
        const preview = document.getElementById('filePreview');
        const fileName = document.getElementById('fileName');
        const fileSize = document.getElementById('fileSize');
        const fileType = document.getElementById('fileType');
        const fileIcon = document.getElementById('fileIconPreview');
        
        if (preview && fileName && fileSize && fileType) {
            fileName.textContent = file.name;
            fileSize.textContent = formatFileSize(file.size);
            fileType.textContent = file.type || 'Unknown';
            
            // Display file icon
            if (fileIcon) {
                fileIcon.innerHTML = `<i class="${getFileIcon(file.name)}" style="font-size: 3rem;"></i>`;
            }
            
            preview.classList.remove('d-none');
        }
    }

    function validateFile(file) {
        // Check file size (16MB limit)
        const maxSize = 16 * 1024 * 1024; // 16MB in bytes
        if (file.size > maxSize) {
            showNotification('File size exceeds 16MB limit. Please choose a smaller file.', 'error');
            return false;
        }

        // Check file type
        const allowedExtensions = ['txt', 'pdf', 'png', 'jpg', 'jpeg', 'gif', 'doc', 'docx', 'xls', 'xlsx', 'ppt', 'pptx', 'zip', 'rar'];
        const fileExtension = file.name.split('.').pop().toLowerCase();

        if (!allowedExtensions.includes(fileExtension)) {
            showNotification('File type not allowed. Please choose an allowed file type.', 'error');
            return false;
        }

        return true;
    }

    // Progress bar simulation
    function simulateUploadProgress() {
        const progressDiv = document.getElementById('uploadProgress');
        const progressBar = document.getElementById('progressBar');
        const progressText = document.getElementById('progressText');
        const uploadStatus = document.getElementById('uploadStatus');
        
        if (progressDiv && progressBar && progressText) {
            progressDiv.classList.remove('d-none');
            let progress = 0;
            
            const interval = setInterval(() => {
                progress += Math.random() * 15;
                if (progress > 90) {
                    progress = 90;
                    clearInterval(interval);
                    uploadStatus.textContent = 'Finalizing upload...';
                } else {
                    uploadStatus.textContent = `Uploading... ${Math.round(progress)}%`;
                }
                
                progressBar.style.width = progress + '%';
                progressText.textContent = Math.round(progress) + '%';
            }, 200);
        }
    }

    // Search functionality
    const searchInput = document.getElementById('searchInput');
    const sortSelect = document.getElementById('sortSelect');
    const filterSelect = document.getElementById('filterSelect');
    
    if (searchInput) {
        searchInput.addEventListener('input', filterFiles);
    }
    
    if (sortSelect) {
        sortSelect.addEventListener('change', filterFiles);
    }
    
    if (filterSelect) {
        filterSelect.addEventListener('change', filterFiles);
    }
    
    function filterFiles() {
        const searchTerm = searchInput ? searchInput.value.toLowerCase() : '';
        const sortBy = sortSelect ? sortSelect.value : 'date_desc';
        const filterBy = filterSelect ? filterSelect.value : 'all';
        
        const fileRows = document.querySelectorAll('tbody tr');
        const files = Array.from(fileRows).map(row => {
            const fileName = row.querySelector('td:first-child').textContent.trim();
            const fileDate = row.querySelector('td:nth-child(2)').textContent;
            return {
                element: row,
                name: fileName,
                date: fileDate
            };
        });
        
        // Filter files
        let filteredFiles = files.filter(file => {
            const matchesSearch = file.name.toLowerCase().includes(searchTerm);
            const matchesFilter = filterBy === 'all' || getFileCategory(file.name) === filterBy;
            return matchesSearch && matchesFilter;
        });
        
        // Sort files
        filteredFiles.sort((a, b) => {
            switch (sortBy) {
                case 'name_asc':
                    return a.name.localeCompare(b.name);
                case 'name_desc':
                    return b.name.localeCompare(a.name);
                case 'date_asc':
                    return new Date(a.date) - new Date(b.date);
                case 'date_desc':
                default:
                    return new Date(b.date) - new Date(a.date);
            }
        });
        
        // Update DOM
        const tbody = document.querySelector('tbody');
        tbody.innerHTML = '';
        filteredFiles.forEach(file => {
            tbody.appendChild(file.element);
        });
        
        // Show/hide no files message
        const noFilesMsg = document.querySelector('.text-center.py-5');
        if (noFilesMsg) {
            noFilesMsg.style.display = filteredFiles.length === 0 ? 'block' : 'none';
        }
    }
    
    function getFileCategory(fileName) {
        const extension = fileName.split('.').pop().toLowerCase();
        const imageTypes = ['jpg', 'jpeg', 'png', 'gif'];
        const documentTypes = ['pdf', 'doc', 'docx', 'txt'];
        const archiveTypes = ['zip', 'rar'];
        
        if (imageTypes.includes(extension)) return 'image';
        if (documentTypes.includes(extension)) return 'document';
        if (archiveTypes.includes(extension)) return 'archive';
        return 'other';
    }

    // File upload validation
    const fileInput = document.getElementById('file');
    if (fileInput) {
        fileInput.addEventListener('change', function(e) {
            const file = e.target.files[0];
            if (file) {
                handleFiles([file]);
            }
        });
    }

    // Copy to clipboard functionality
    window.copyToClipboard = function(text) {
        const textarea = document.createElement('textarea');
        textarea.value = text;
        textarea.style.position = 'fixed';
        textarea.style.opacity = '0';
        document.body.appendChild(textarea);
        textarea.select();
        
        try {
            document.execCommand('copy');
            showNotification('Link copied to clipboard!', 'success');
        } catch (err) {
            console.error('Failed to copy text: ', err);
            showNotification('Failed to copy link', 'error');
        }
        
        document.body.removeChild(textarea);
    };

    // Show notification
    window.showNotification = function(message, type) {
        const notification = document.createElement('div');
        notification.className = `alert alert-${type} alert-dismissible fade show position-fixed`;
        notification.style.top = '20px';
        notification.style.right = '20px';
        notification.style.zIndex = '9999';
        notification.innerHTML = `
            ${message}
            <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
        `;
        
        document.body.appendChild(notification);
        
        setTimeout(() => {
            notification.remove();
        }, 3000);
    };

    // Format file size
    window.formatFileSize = function(bytes) {
        if (bytes === 0) return '0 Bytes';
        const k = 1024;
        const sizes = ['Bytes', 'KB', 'MB', 'GB'];
        const i = Math.floor(Math.log(bytes) / Math.log(k));
        return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
    };

    // Get file icon based on extension
    window.getFileIcon = function(filename) {
        const extension = filename.split('.').pop().toLowerCase();
        const iconMap = {
            'pdf': 'bi-file-earmark-pdf text-danger',
            'doc': 'bi-file-earmark-word text-primary',
            'docx': 'bi-file-earmark-word text-primary',
            'xls': 'bi-file-earmark-excel text-success',
            'xlsx': 'bi-file-earmark-excel text-success',
            'ppt': 'bi-file-earmark-ppt text-warning',
            'pptx': 'bi-file-earmark-ppt text-warning',
            'jpg': 'bi-file-earmark-image text-info',
            'jpeg': 'bi-file-earmark-image text-info',
            'png': 'bi-file-earmark-image text-info',
            'gif': 'bi-file-earmark-image text-info',
            'zip': 'bi-file-earmark-archive text-secondary',
            'rar': 'bi-file-earmark-archive text-secondary',
            'txt': 'bi-file-earmark-text text-muted'
        };
        
        return iconMap[extension] || 'bi-file-earmark text-muted';
    };

    // Confirm delete action
    const deleteButtons = document.querySelectorAll('[onclick*="confirm"]');
    deleteButtons.forEach(button => {
        button.addEventListener('click', function(e) {
            if (!confirm('Are you sure you want to delete this file?')) {
                e.preventDefault();
            }
        });
    });

    // Add loading state to forms
    const forms = document.querySelectorAll('form');
    forms.forEach(form => {
        form.addEventListener('submit', function(e) {
            const submitButton = form.querySelector('button[type="submit"]');
            if (submitButton && form.id === 'uploadForm') {
                e.preventDefault();
                
                if (!validateSelectedFile()) {
                    return;
                }
                
                const originalText = submitButton.innerHTML;
                submitButton.innerHTML = '<span class="spinner-border spinner-border-sm me-2"></span>Uploading...';
                submitButton.disabled = true;
                
                // Start progress simulation
                simulateUploadProgress();
                
                // Submit form after a short delay
                setTimeout(() => {
                    form.submit();
                }, 500);
                
                // Re-enable after 10 seconds (fallback)
                setTimeout(() => {
                    submitButton.innerHTML = originalText;
                    submitButton.disabled = false;
                }, 10000);
            } else if (submitButton) {
                const originalText = submitButton.innerHTML;
                submitButton.innerHTML = '<span class="spinner-border spinner-border-sm me-2"></span>Loading...';
                submitButton.disabled = true;
                
                // Re-enable after 10 seconds (fallback)
                setTimeout(() => {
                    submitButton.innerHTML = originalText;
                    submitButton.disabled = false;
                }, 10000);
            }
        });
    });
    
    function validateSelectedFile() {
        const fileInput = document.getElementById('file');
        if (fileInput && fileInput.files.length > 0) {
            return validateFile(fileInput.files[0]);
        }
        return false;
    }
});

// Theme Management
function initializeTheme() {
    // Check for saved theme preference or system preference
    const savedTheme = localStorage.getItem('theme');
    const systemPrefersDark = window.matchMedia('(prefers-color-scheme: dark)').matches;
    
    // Apply theme
    if (savedTheme === 'dark' || (!savedTheme && systemPrefersDark)) {
        document.body.classList.add('dark-theme');
        updateThemeIcon(true);
    } else {
        document.body.classList.remove('dark-theme');
        updateThemeIcon(false);
    }
    
    // Add event listener for theme toggle
    const themeToggle = document.getElementById('themeToggle');
    if (themeToggle) {
        themeToggle.addEventListener('click', toggleTheme);
    }
    
    // Listen for system theme changes
    window.matchMedia('(prefers-color-scheme: dark)').addEventListener('change', (e) => {
        if (!localStorage.getItem('theme')) {
            // Only apply system preference if user hasn't manually set a preference
            if (e.matches) {
                document.body.classList.add('dark-theme');
                updateThemeIcon(true);
            } else {
                document.body.classList.remove('dark-theme');
                updateThemeIcon(false);
            }
        }
    });
}

function toggleTheme() {
    const isDark = document.body.classList.contains('dark-theme');
    
    if (isDark) {
        document.body.classList.remove('dark-theme');
        localStorage.setItem('theme', 'light');
        updateThemeIcon(false);
    } else {
        document.body.classList.add('dark-theme');
        localStorage.setItem('theme', 'dark');
        updateThemeIcon(true);
    }
}

function updateThemeIcon(isDark) {
    const themeIcon = document.getElementById('themeIcon');
    if (themeIcon) {
        if (isDark) {
            themeIcon.classList.remove('bi-moon');
            themeIcon.classList.add('bi-sun');
        } else {
            themeIcon.classList.remove('bi-sun');
            themeIcon.classList.add('bi-moon');
        }
    }
}

// Utility functions
function debounce(func, wait) {
    let timeout;
    return function executedFunction(...args) {
        const later = () => {
            clearTimeout(timeout);
            func(...args);
        };
        clearTimeout(timeout);
        timeout = setTimeout(later, wait);
    };
}

function throttle(func, limit) {
    let inThrottle;
    return function() {
        const args = arguments;
        const context = this;
        if (!inThrottle) {
            func.apply(context, args);
            inThrottle = true;
            setTimeout(() => inThrottle = false, limit);
        }
    };
}
