class ProfileManager {
    constructor() {
        if (!Utils.requireAuth()) return;
        Utils.updateAuthNav('profile');
        this.farmers = [];
        this.init();
    }

    async init() {
        this.bindForm();
        await Promise.all([this.loadAccount(), this.loadFarmers()]);
    }

    bindForm() {
        document.getElementById('farmerForm').addEventListener('submit', (event) => this.saveFarmer(event));
        document.getElementById('resetFormButton').addEventListener('click', () => this.resetForm());
    }

    async loadAccount() {
        const user = await Utils.apiRequest(API_CONFIG.getEndpoint('AUTH_ME'));
        document.getElementById('accountSummary').innerHTML = `
            <div><strong>${user.username}</strong></div>
            <div>${user.email || 'No email added'}</div>
        `;
    }

    async loadFarmers() {
        const data = await Utils.apiRequest(API_CONFIG.getEndpoint('FARMERS'));
        this.farmers = data.results || data;
        this.renderFarmers();
    }

    renderFarmers() {
        const container = document.getElementById('farmersContainer');
        if (!this.farmers.length) {
            container.innerHTML = '<div class="col-12"><div class="alert alert-info">No farmer profiles yet.</div></div>';
            return;
        }

        container.innerHTML = this.farmers.map(farmer => `
            <div class="col-md-6">
                <div class="feature-card h-100">
                    <h3 class="feature-title">${farmer.full_name}</h3>
                    <p class="mb-2"><i class="bi bi-telephone-fill text-success me-2"></i>${farmer.phone_number}</p>
                    <p class="mb-2"><i class="bi bi-geo-alt-fill text-success me-2"></i>${farmer.location}</p>
                    <p class="mb-3"><span class="badge bg-primary">${farmer.region_code}</span></p>
                    <div class="d-flex gap-2">
                        <button class="btn btn-sm btn-outline-primary" data-action="edit" data-id="${farmer.id}">Edit</button>
                        <button class="btn btn-sm btn-outline-danger" data-action="delete" data-id="${farmer.id}">Delete</button>
                    </div>
                </div>
            </div>
        `).join('');

        container.querySelectorAll('button[data-action]').forEach(button => {
            button.addEventListener('click', () => {
                const farmer = this.farmers.find(item => item.id == button.dataset.id);
                if (button.dataset.action === 'edit') this.editFarmer(farmer);
                if (button.dataset.action === 'delete') this.deleteFarmer(farmer);
            });
        });
    }

    async saveFarmer(event) {
        event.preventDefault();
        const farmerId = document.getElementById('farmerId').value;
        const payload = {
            full_name: document.getElementById('farmerName').value,
            phone_number: document.getElementById('farmerPhone').value,
            email: document.getElementById('farmerEmail').value,
            location: document.getElementById('farmerLocation').value,
            region_code: document.getElementById('farmerRegion').value,
            gender: document.getElementById('farmerGender').value,
            farm_size_hectares: document.getElementById('farmerFarmSize').value || null,
        };

        const url = farmerId ? `${API_CONFIG.getEndpoint('FARMERS')}${farmerId}/` : API_CONFIG.getEndpoint('FARMERS');
        await Utils.apiRequest(url, {
            method: farmerId ? 'PATCH' : 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(payload),
        });
        Utils.showToast('Farmer profile saved', 'success');
        this.resetForm();
        await this.loadFarmers();
    }

    editFarmer(farmer) {
        document.getElementById('formTitle').textContent = 'Edit Farmer';
        document.getElementById('farmerId').value = farmer.id;
        document.getElementById('farmerName').value = farmer.full_name || '';
        document.getElementById('farmerPhone').value = farmer.phone_number || '';
        document.getElementById('farmerEmail').value = farmer.email || '';
        document.getElementById('farmerLocation').value = farmer.location || '';
        document.getElementById('farmerRegion').value = farmer.region_code || '';
        document.getElementById('farmerGender').value = farmer.gender || '';
        document.getElementById('farmerFarmSize').value = farmer.farm_size_hectares || '';
    }

    async deleteFarmer(farmer) {
        if (!confirm(`Delete ${farmer.full_name}?`)) return;
        await Utils.apiRequest(`${API_CONFIG.getEndpoint('FARMERS')}${farmer.id}/`, { method: 'DELETE' });
        Utils.showToast('Farmer profile deleted', 'success');
        await this.loadFarmers();
    }

    resetForm() {
        document.getElementById('formTitle').textContent = 'Add Farmer';
        document.getElementById('farmerForm').reset();
        document.getElementById('farmerId').value = '';
    }
}

document.addEventListener('DOMContentLoaded', () => new ProfileManager());
