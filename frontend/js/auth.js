document.addEventListener('DOMContentLoaded', () => {
    Utils.updateAuthNav();

    const resetConfirmForm = document.getElementById('resetConfirmForm');
    if (resetConfirmForm) {
        bindResetConfirmForm(resetConfirmForm);
        return;
    }

    const next = new URLSearchParams(window.location.search).get('next') || 'profile.html';
    const registerTab = new bootstrap.Tab(document.getElementById('register-tab'));
    const resetTab = new bootstrap.Tab(document.getElementById('reset-tab'));

    document.getElementById('showRegisterButton').addEventListener('click', () => registerTab.show());
    document.getElementById('showResetButton').addEventListener('click', () => resetTab.show());

    document.getElementById('loginForm').addEventListener('submit', async (event) => {
        event.preventDefault();
        try {
            const session = await Utils.apiRequest(API_CONFIG.getEndpoint('AUTH_LOGIN'), {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    username: document.getElementById('loginUsername').value,
                    password: document.getElementById('loginPassword').value,
                }),
            });
            Utils.setAuth(session);
            window.location.href = next;
        } catch (error) {
            Utils.showToast(error.message, 'danger');
        }
    });

    document.getElementById('registerForm').addEventListener('submit', async (event) => {
        event.preventDefault();
        try {
            const session = await Utils.apiRequest(API_CONFIG.getEndpoint('AUTH_REGISTER'), {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    username: document.getElementById('registerUsername').value,
                    email: document.getElementById('registerEmail').value,
                    password: document.getElementById('registerPassword').value,
                }),
            });
            Utils.setAuth(session);
            window.location.href = next;
        } catch (error) {
            Utils.showToast(error.message, 'danger');
        }
    });

    document.getElementById('resetRequestForm').addEventListener('submit', async (event) => {
        event.preventDefault();
        const container = document.getElementById('resetLinkContainer');

        try {
            const response = await Utils.apiRequest(API_CONFIG.getEndpoint('AUTH_PASSWORD_RESET'), {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    identifier: document.getElementById('resetIdentifier').value,
                }),
            });

            container.style.display = 'block';
            container.innerHTML = response.reset_url
                ? `Reset link: <a href="${response.reset_url.replace(API_CONFIG.BASE_URL, '')}">open reset form</a>`
                : response.detail;
            Utils.showToast('Password reset request processed', 'success');
        } catch (error) {
            Utils.showToast(error.message, 'danger');
        }
    });
});

function bindResetConfirmForm(form) {
    const params = new URLSearchParams(window.location.search);
    const uid = params.get('uid');
    const token = params.get('token');

    if (!uid || !token) {
        Utils.showToast('Invalid password reset link', 'danger');
        form.querySelector('button[type="submit"]').disabled = true;
        return;
    }

    form.addEventListener('submit', async (event) => {
        event.preventDefault();
        const newPassword = document.getElementById('newPassword').value;
        const confirmPassword = document.getElementById('confirmPassword').value;

        if (newPassword !== confirmPassword) {
            Utils.showToast('Passwords do not match', 'danger');
            return;
        }

        try {
            const session = await Utils.apiRequest(API_CONFIG.getEndpoint('AUTH_PASSWORD_RESET_CONFIRM'), {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    uid,
                    token,
                    new_password: newPassword,
                }),
            });
            Utils.setAuth(session);
            Utils.showToast('Password reset successfully', 'success');
            window.location.href = 'profile.html';
        } catch (error) {
            Utils.showToast(error.message, 'danger');
        }
    });
}
