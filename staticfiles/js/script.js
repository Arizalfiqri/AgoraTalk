// ====== AGORATALK NAVBAR JAVASCRIPT ======
document.addEventListener("DOMContentLoaded", function () {
  // Mobile menu toggle
  const mobileMenuBtn = document.getElementById("mobileMenuBtn");
  const mobileMenu = document.getElementById("mobileMenu");

  if (mobileMenuBtn && mobileMenu) {
    mobileMenuBtn.addEventListener("click", function () {
      mobileMenu.classList.toggle("hidden");
      const icon = mobileMenuBtn.querySelector("i");
      if (mobileMenu.classList.contains("hidden")) {
        icon.classList.remove("fa-times");
        icon.classList.add("fa-bars");
      } else {
        icon.classList.remove("fa-bars");
        icon.classList.add("fa-times");
      }
    });
  }

  // User menu toggle
  const userMenuBtn = document.getElementById("userMenuBtn");
  const userMenu = document.getElementById("userMenu");

  if (userMenuBtn && userMenu) {
    userMenuBtn.addEventListener("click", function (e) {
      e.preventDefault();
      e.stopPropagation();

      // Toggle user menu with animation
      if (userMenu.classList.contains("hidden")) {
        userMenu.classList.remove("hidden");
        setTimeout(() => userMenu.classList.add("show"), 10);
      } else {
        userMenu.classList.remove("show");
        setTimeout(() => userMenu.classList.add("hidden"), 200);
      }

      // Close notification menu if open
      const notificationMenu = document.getElementById("notificationMenu");
      if (
        notificationMenu &&
        !notificationMenu.classList.contains("hidden")
      ) {
        notificationMenu.classList.remove("show");
        setTimeout(() => notificationMenu.classList.add("hidden"), 200);
      }
    });
  }

  // Notification menu toggle
  const notificationBtn = document.getElementById("notificationBtn");
  const notificationMenu = document.getElementById("notificationMenu");

  if (notificationBtn && notificationMenu) {
    notificationBtn.addEventListener("click", function (e) {
      e.preventDefault();
      e.stopPropagation();

      // Toggle notification menu with animation
      if (notificationMenu.classList.contains("hidden")) {
        notificationMenu.classList.remove("hidden");
        setTimeout(() => notificationMenu.classList.add("show"), 10);
      } else {
        notificationMenu.classList.remove("show");
        setTimeout(() => notificationMenu.classList.add("hidden"), 200);
      }

      // Close user menu if open
      if (userMenu && !userMenu.classList.contains("hidden")) {
        userMenu.classList.remove("show");
        setTimeout(() => userMenu.classList.add("hidden"), 200);
      }
    });
  }

  // Close dropdowns when clicking outside
  document.addEventListener("click", function (e) {
    if (
      userMenu &&
      userMenuBtn &&
      !userMenu.contains(e.target) &&
      !userMenuBtn.contains(e.target)
    ) {
      userMenu.classList.remove("show");
      setTimeout(() => userMenu.classList.add("hidden"), 200);
    }
    if (
      notificationMenu &&
      notificationBtn &&
      !notificationMenu.contains(e.target) &&
      !notificationBtn.contains(e.target)
    ) {
      notificationMenu.classList.remove("show");
      setTimeout(() => notificationMenu.classList.add("hidden"), 200);
    }
  });

  // Search form validation
  const searchForm = document.getElementById("searchForm");
  if (searchForm) {
    searchForm.addEventListener("submit", function (e) {
      const input = searchForm.querySelector('input[name="q"]');
      const value = input.value.trim();

      if (value.length < 2) {
        e.preventDefault();
        alert("Kata kunci pencarian minimal 2 karakter");
        input.focus();
        return false;
      }

      if (value.length > 100) {
        e.preventDefault();
        alert("Kata kunci pencarian maksimal 100 karakter");
        input.focus();
        return false;
      }
    });
  }

  // Load notifications
  loadNotifications();
  setInterval(loadNotifications, 30000);
});

// Notification functions
function loadNotifications() {
  fetch("/notifications/")
    .then((response) => response.json())
    .then((data) => {
      const badge = document.getElementById("notificationBadge");
      const list = document.getElementById("notificationList");

      if (data.count > 0) {
        badge.textContent = data.count;
        badge.classList.remove("hidden");

        list.innerHTML = "";
        data.notifications.forEach((notification) => {
          const item = document.createElement("div");
          item.className = "p-3 border-b hover:bg-gray-50 cursor-pointer";
          item.innerHTML = `
                      <div class="flex items-start space-x-3">
                          <div class="flex-shrink-0">
                              ${getNotificationIcon(notification.type)}
                          </div>
                          <div class="flex-1">
                              <p class="text-sm text-gray-800">${
                                notification.message
                              }</p>
                              <p class="text-xs text-gray-500 mt-1">${
                                notification.created_at
                              }</p>
                          </div>
                          <button onclick="markAsRead(${
                            notification.id
                          })" class="text-gray-400 hover:text-gray-600">
                              <i class="fas fa-check text-xs"></i>
                          </button>
                      </div>
                  `;

          if (notification.thread_url) {
            item.addEventListener("click", function (e) {
              if (!e.target.closest("button")) {
                window.location.href = notification.thread_url;
              }
            });
          }

          list.appendChild(item);
        });
      } else {
        badge.classList.add("hidden");
        list.innerHTML = `
                  <div class="p-6 text-center text-gray-500">
                      <i class="fas fa-bell-slash text-2xl mb-2"></i>
                      <p>Tidak ada notifikasi baru</p>
                  </div>
              `;
      }
    })
    .catch((error) => console.error("Error loading notifications:", error));
}

function getNotificationIcon(type) {
  const icons = {
    reply: '<i class="fas fa-reply text-blue-500"></i>',
    mention: '<i class="fas fa-at text-cyan-500"></i>',
    vote: '<i class="fas fa-thumbs-up text-green-500"></i>',
  };
  return icons[type] || '<i class="fas fa-bell text-gray-500"></i>';
}

function markAsRead(notificationId) {
  fetch(`/notifications/mark-read/${notificationId}/`, {
    method: "POST",
    headers: {
      "X-CSRFToken": getCookie("csrftoken"),
      "Content-Type": "application/json",
    },
  })
    .then((response) => response.json())
    .then((data) => {
      if (data.success) {
        loadNotifications();
      }
    })
    .catch((error) =>
      console.error("Error marking notification as read:", error)
    );
}

function markAllNotificationsRead() {
  fetch("/notifications/mark-all-read/", {
    method: "POST",
    headers: {
      "X-CSRFToken": getCookie("csrftoken"),
      "Content-Type": "application/json",
    },
  })
    .then((response) => response.json())
    .then((data) => {
      if (data.success) {
        loadNotifications();
      }
    })
    .catch((error) =>
      console.error("Error marking all notifications as read:", error)
    );
}

function getCookie(name) {
  let cookieValue = null;
  if (document.cookie && document.cookie !== "") {
    const cookies = document.cookie.split(";");
    for (let i = 0; i < cookies.length; i++) {
      const cookie = cookies[i].trim();
      if (cookie.substring(0, name.length + 1) === name + "=") {
        cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
        break;
      }
    }
  }
  return cookieValue;
}
// ====== END AGORATALK NAVBAR JAVASCRIPT ======

// ====== CREATE THREAD PAGE FUNCTIONALITY ======
function initCreateThreadPage() {
    // Only run on create thread page
    if (!document.getElementById('createThreadForm')) {
        return;
    }

    // Auto-resize textarea
    const textarea = document.querySelector('#id_content');
    if (textarea) {
        textarea.addEventListener('input', function() {
            this.style.height = 'auto';
            this.style.height = this.scrollHeight + 'px';
        });
    }
    
    // Image upload preview functionality
    const imageInput = document.getElementById('id_image');
    const uploadPlaceholder = document.getElementById('upload-placeholder');
    const imagePreview = document.getElementById('image-preview');
    const previewImg = document.getElementById('preview-img');
    const removeImageBtn = document.getElementById('remove-image');
    
    if (imageInput) {
        // Hide the default file input
        imageInput.style.display = 'none';
        
        imageInput.addEventListener('change', function(e) {
            const file = e.target.files[0];
            if (file) {
                // Validate file size (1MB = 1024 * 1024 bytes)
                if (file.size > 1024 * 1024) {
                    alert('Ukuran file terlalu besar! Maksimal 1MB.');
                    this.value = '';
                    return;
                }
                
                // Validate file type
                if (!file.type.startsWith('image/')) {
                    alert('File harus berupa gambar!');
                    this.value = '';
                    return;
                }
                
                // Show preview
                const reader = new FileReader();
                reader.onload = function(e) {
                    previewImg.src = e.target.result;
                    uploadPlaceholder.style.display = 'none';
                    imagePreview.classList.remove('hidden');
                };
                reader.readAsDataURL(file);
            }
        });
        
        // Remove image functionality
        if (removeImageBtn) {
            removeImageBtn.addEventListener('click', function() {
                imageInput.value = '';
                uploadPlaceholder.style.display = 'flex';
                imagePreview.classList.add('hidden');
                previewImg.src = '';
            });
        }
    }
    
    // Form validation
    const form = document.getElementById('createThreadForm');
    if (form) {
        form.addEventListener('submit', function(e) {
            let isValid = true;
            const requiredFields = ['id_title', 'id_category', 'id_content'];
            
            requiredFields.forEach(fieldId => {
                const field = document.getElementById(fieldId);
                if (field && !field.value.trim()) {
                    isValid = false;
                    field.classList.add('is-invalid');
                } else if (field) {
                    field.classList.remove('is-invalid');
                }
            });
            
            // Validate image size if uploaded
            const imageFile = imageInput ? imageInput.files[0] : null;
            if (imageFile && imageFile.size > 1024 * 1024) {
                isValid = false;
                alert('Ukuran gambar terlalu besar! Maksimal 1MB.');
            }
            
            if (!isValid) {
                e.preventDefault();
                // Remove existing alerts
                const existingAlerts = form.querySelectorAll('.form-alert');
                existingAlerts.forEach(alert => alert.remove());
                
                // Show error alert
                const alertDiv = document.createElement('div');
                alertDiv.className = 'form-alert';
                alertDiv.innerHTML = `
                    <i class="fas fa-exclamation-circle mr-2"></i>
                    <span>Mohon lengkapi semua field yang wajib diisi.</span>
                    <button type="button" class="alert-close" onclick="this.parentElement.remove()">
                        <i class="fas fa-times"></i>
                    </button>
                `;
                form.prepend(alertDiv);
                
                // Scroll to top of form
                form.scrollIntoView({ behavior: 'smooth', block: 'start' });
            }
        });
    }
    
    // Character counter for title
    const titleField = document.getElementById('id_title');
    if (titleField) {
        const maxLength = 255;
        const counter = document.createElement('div');
        counter.className = 'char-counter';
        titleField.parentNode.appendChild(counter);
        
        function updateCounter() {
            const remaining = maxLength - titleField.value.length;
            counter.textContent = `${remaining} karakter tersisa`;
            if (remaining < 20) {
                counter.className = 'char-counter warning';
            } else {
                counter.className = 'char-counter';
            }
        }
        
        titleField.addEventListener('input', updateCounter);
        updateCounter();
    }

    // Drag and drop functionality for image upload
    const uploadArea = document.querySelector('.image-upload-area');
    if (uploadArea && imageInput) {
        uploadArea.addEventListener('dragover', function(e) {
            e.preventDefault();
            this.style.backgroundColor = '#f3f4f6';
            this.style.borderColor = '#06b6d4';
        });

        uploadArea.addEventListener('dragleave', function(e) {
            e.preventDefault();
            this.style.backgroundColor = '#f9fafb';
            this.style.borderColor = '#d1d5db';
        });

        uploadArea.addEventListener('drop', function(e) {
            e.preventDefault();
            this.style.backgroundColor = '#f9fafb';
            this.style.borderColor = '#d1d5db';
            
            const files = e.dataTransfer.files;
            if (files.length > 0) {
                imageInput.files = files;
                imageInput.dispatchEvent(new Event('change'));
            }
        });
    }
}

// Initialize create thread functionality when DOM is loaded
document.addEventListener('DOMContentLoaded', initCreateThreadPage);
// ====== END CREATE THREAD PAGE FUNCTIONALITY ======
