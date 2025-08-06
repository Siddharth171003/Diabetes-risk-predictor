// Initialize when document is ready
document.addEventListener('DOMContentLoaded', function() {
    initializeFormValidation();
    initializeAdminPatientValidation();
    initializeRegisterValidation();
    initializeLoginValidation();
    initializeProgressBars();
    initializeTooltips();
    initializeHealthCalculators();
});

// ----------------------
// Existing Validation
// ----------------------
function initializeFormValidation() {
    const form = document.querySelector('form');
    if (!form) return;
    const inputs = form.querySelectorAll('input[type="number"]');
    inputs.forEach(input => {
        input.addEventListener('input', function() {
            validateInput(this);
            calculateRiskPreview();
        });
        input.addEventListener('blur', function() {
            showHealthTips(this);
        });
    });
}

// (validateInput, showInputError, hideInputError, showHealthTips, getHealthTip,
//  initializeHealthCalculators, calculateBMI, calculateRiskPreview, showRiskPreview,
//  initializeProgressBars, initializeTooltips, showTooltip, showLoading, etc.)
// — keep all your existing functions unchanged here —

// ----------------------
// Admin Patient Validation
// ----------------------
function initializeAdminPatientValidation() {
    const form = document.querySelector('form#admin-add-form');
    if (!form) return;

    form.addEventListener('submit', function(event) {
        let valid = true;

        // Clear all previous errors
        document.querySelectorAll('.error-message').forEach(e => e.textContent = '');
        document.querySelectorAll('.form-control').forEach(el => el.classList.remove('is-invalid'));

        // Name
        const name = form.name.value.trim();
        if (!/^[A-Za-z ]{3,}$/.test(name)) {
            document.getElementById('name-error').textContent = 'Name must be at least 3 letters (only alphabets and spaces).';
            form.name.classList.add('is-invalid');
            valid = false;
        }

        // Phone
        const phone = form.phone.value.trim();
        if (!/^\d{10,15}$/.test(phone)) {
            document.getElementById('phone-error').textContent = 'Phone must be 10–15 digits.';
            form.phone.classList.add('is-invalid');
            valid = false;
        }

        // Email (HTML5 handles this, but we'll show message)
        if (!form.email.checkValidity()) {
            document.getElementById('email-error').textContent = 'Enter a valid email address.';
            form.email.classList.add('is-invalid');
            valid = false;
        }

        if (!valid) event.preventDefault();
    });
}

// ----------------------
// Register Page Validation
// ----------------------
function initializeRegisterValidation() {
    const form = document.querySelector('form#register-form');
    if (!form) return;

    form.addEventListener('submit', function(event) {
        let valid = true;

        // Email
        if (!form.email.checkValidity()) {
            valid = false;
            showInputError(form.email, 'Enter a valid email address.');
        } else {
            hideInputError(form.email);
        }

        // Password: ≥8 chars, uppercase, digit, special
        const pw = form.password.value;
        const pwPattern = /^(?=.*[A-Z])(?=.*\d)(?=.*[@$!%*?&]).{8,}$/;
        if (!pwPattern.test(pw)) {
            valid = false;
            showInputError(form.password,
                'Password must be ≥8 chars, include uppercase, number, special char.');
        } else {
            hideInputError(form.password);
        }

        // Confirm Password
        if (form.confirm_password.value !== pw) {
            valid = false;
            showInputError(form.confirm_password, 'Passwords do not match.');
        } else {
            hideInputError(form.confirm_password);
        }

        if (!valid) event.preventDefault();
    });
}

// ----------------------
// Login Page Validation
// ----------------------
function initializeLoginValidation() {
    const form = document.querySelector('form#login-form');
    if (!form) return;

    form.addEventListener('submit', function(event) {
        let valid = true;

        // Password: min length 8
        const pw = form.password.value;
        if (pw.length < 8) {
            valid = false;
            showInputError(form.password, 'Password must be at least 8 characters.');
        } else {
            hideInputError(form.password);
        }

        if (!valid) event.preventDefault();
    });
}


function showInputError(inputElement, message) {
    let errorDiv = inputElement.parentElement.querySelector('.error-message');
    if (!errorDiv) {
        errorDiv = document.createElement('div');
        errorDiv.className = 'error-message text-danger mt-1';
        inputElement.parentElement.appendChild(errorDiv);
    }
    errorDiv.textContent = message;
    inputElement.classList.add('is-invalid');
}

function hideInputError(inputElement) {
    const errorDiv = inputElement.parentElement.querySelector('.error-message');
    if (errorDiv) errorDiv.textContent = '';
    inputElement.classList.remove('is-invalid');
}