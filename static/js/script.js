document.addEventListener('DOMContentLoaded', function() {
    // Mobile menu toggle
    const mobileMenuToggle = document.querySelector('.mobile-menu-toggle');
    const mainNav = document.querySelector('.main-nav');

    if (mobileMenuToggle) {
        mobileMenuToggle.addEventListener('click', function() {
            mainNav.classList.toggle('active');
        });
    }

    // File upload dropzone functionality
    const dropzone = document.getElementById('dropzone');
    const fileInput = document.getElementById('xrayInput');
    const analyzeButton = document.getElementById('analyzeButton');

    if (dropzone) {
        // Prevent default drag behaviors
        ['dragenter', 'dragover', 'dragleave', 'drop'].forEach(eventName => {
            dropzone.addEventListener(eventName, preventDefaults, false);
        });

        // Highlight dropzone when item is dragged over it
        ['dragenter', 'dragover'].forEach(eventName => {
            dropzone.addEventListener(eventName, highlight, false);
        });

        ['dragleave', 'drop'].forEach(eventName => {
            dropzone.addEventListener(eventName, unhighlight, false);
        });

        // Handle dropped files
        dropzone.addEventListener('drop', handleDrop, false);

        // Handle file selection via button
        fileInput.addEventListener('change', function() {
            if (this.files.length) {
                updateThumbnail(dropzone, this.files[0]);
                analyzeButton.disabled = false;
            }
        });
    }

    function preventDefaults(e) {
        e.preventDefault();
        e.stopPropagation();
    }

    function highlight() {
        dropzone.classList.add('dragover');
    }

    function unhighlight() {
        dropzone.classList.remove('dragover');
    }

    function handleDrop(e) {
        const dt = e.dataTransfer;
        const files = dt.files;

        if (files.length) {
            fileInput.files = files;
            updateThumbnail(dropzone, files[0]);
            analyzeButton.disabled = false;
        }
    }

    function updateThumbnail(dropzone, file) {
        const reader = new FileReader();

        reader.onload = function(e) {
            const thumbnail = document.createElement('div');
            thumbnail.classList.add('thumbnail');
            thumbnail.innerHTML = `
                <div class="thumbnail-inner">
                    <img src="${e.target.result}" alt="${file.name}">
                    <div class="thumbnail-info">
                        <span>${file.name}</span>
                        <span>${(file.size / 1024 / 1024).toFixed(2)} MB</span>
                    </div>
                </div>
            `;

            // Remove any existing thumbnails
            const existingThumbnail = dropzone.querySelector('.thumbnail');
            if (existingThumbnail) {
                dropzone.removeChild(existingThumbnail);
            }

            // Remove the default upload prompt
            const uploadLabel = dropzone.querySelector('.upload-label');
            if (uploadLabel) {
                uploadLabel.style.display = 'none';
            }

            dropzone.appendChild(thumbnail);
        };

        reader.readAsDataURL(file);
    }
});

// Image modal functionality
function zoomImage() {
    const modal = document.getElementById('imageModal');
    const modalImg = document.getElementById('modalImage');
    const xrayPreview = document.querySelector('.xray-preview');

    modal.style.display = "block";
    modalImg.src = xrayPreview.src;
}

function closeModal() {
    document.getElementById('imageModal').style.display = "none";
}

// Close modal when clicking outside the image
window.onclick = function(event) {
    const modal = document.getElementById('imageModal');
    if (event.target == modal) {
        modal.style.display = "none";
    }
}