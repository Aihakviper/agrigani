/**
 * AgriGani History Page
 * Display and filter diagnosis history
 */

class HistoryManager {
    constructor() {
        this.diagnoses = [];
        this.farmers = [];
        this.diseases = [];
        this.filters = {
            farmer_id: '',
            disease_id: '',
            region_code: ''
        };
        
        this.init();
    }

    async init() {
        await this.loadData();
        this.setupFilters();
        this.renderHistory();
    }

    async loadData() {
        try {
            // Load all data in parallel
            const [diagnosesData, farmersData, diseasesData] = await Promise.all([
                Utils.apiRequest(API_CONFIG.getEndpoint('DIAGNOSES')),
                Utils.apiRequest(API_CONFIG.getEndpoint('FARMERS')),
                Utils.apiRequest(API_CONFIG.getEndpoint('DISEASES'))
            ]);

            this.diagnoses = diagnosesData.results || diagnosesData;
            this.farmers = farmersData.results || farmersData;
            this.diseases = diseasesData.results || diseasesData;

            this.populateFilterDropdowns();
        } catch (error) {
            console.error('Error loading data:', error);
            Utils.showToast('Error loading history', 'danger');
        }
    }

    populateFilterDropdowns() {
        // Populate farmer filter
        const farmerSelect = document.getElementById('filterFarmer');
        this.farmers.forEach(farmer => {
            const option = document.createElement('option');
            option.value = farmer.id;
            option.textContent = `${farmer.full_name} (${farmer.phone_number})`;
            farmerSelect.appendChild(option);
        });

        // Populate disease filter
        const diseaseSelect = document.getElementById('filterDisease');
        this.diseases.forEach(disease => {
            const option = document.createElement('option');
            option.value = disease.id;
            option.textContent = disease.name;
            diseaseSelect.appendChild(option);
        });
    }

    setupFilters() {
        document.getElementById('filterFarmer').addEventListener('change', (e) => {
            this.filters.farmer_id = e.target.value;
            this.renderHistory();
        });

        document.getElementById('filterDisease').addEventListener('change', (e) => {
            this.filters.disease_id = e.target.value;
            this.renderHistory();
        });

        document.getElementById('filterRegion').addEventListener('change', (e) => {
            this.filters.region_code = e.target.value;
            this.renderHistory();
        });
    }

    getFilteredDiagnoses() {
        return this.diagnoses.filter(diagnosis => {
            if (this.filters.farmer_id && diagnosis.farmer != this.filters.farmer_id) {
                return false;
            }
            if (this.filters.disease_id && diagnosis.disease != this.filters.disease_id) {
                return false;
            }
            if (this.filters.region_code && diagnosis.region_code !== this.filters.region_code) {
                return false;
            }
            return true;
        });
    }

    renderHistory() {
        const container = document.getElementById('historyContainer');
        const loadingSpinner = document.getElementById('loadingSpinner');
        const emptyState = document.getElementById('emptyState');

        const filteredDiagnoses = this.getFilteredDiagnoses();

        loadingSpinner.style.display = 'none';

        if (filteredDiagnoses.length === 0) {
            container.style.display = 'none';
            emptyState.style.display = 'block';
            return;
        }

        emptyState.style.display = 'none';
        container.style.display = 'block';

        const html = filteredDiagnoses.map(diagnosis => {
            const confidence = Number(diagnosis.confidence_score || 0);
            return `
            <div class="history-item">
                <div class="history-header">
                    <div>
                        <h3 class="history-disease">${diagnosis.disease_name || 'Unknown Disease'}</h3>
                        <p class="history-date">
                            <i class="bi bi-calendar3 me-2"></i>${Utils.formatDate(diagnosis.created_at)}
                        </p>
                    </div>
                    <div class="confidence-badge ${Utils.getConfidenceClass(confidence)}">
                        ${confidence.toFixed(1)}%
                    </div>
                </div>

                <div class="history-meta">
                    <div class="history-meta-item">
                        <i class="bi bi-person-fill"></i>
                        <span>${diagnosis.farmer_name}</span>
                    </div>
                    ${diagnosis.location ? `
                        <div class="history-meta-item">
                            <i class="bi bi-geo-alt-fill"></i>
                            <span>${diagnosis.location}</span>
                        </div>
                    ` : ''}
                </div>

                ${diagnosis.image_url ? `
                    <div class="mb-3">
                        <img src="${diagnosis.image_url}" 
                             alt="Diagnosis Image" 
                             class="history-image"
                             onclick="window.open('${diagnosis.image_url}', '_blank')">
                    </div>
                ` : ''}

                <div class="mt-3">
                    <a href="diagnosis-detail.html?id=${diagnosis.id}" class="btn btn-sm btn-outline-primary">
                        <i class="bi bi-eye me-2"></i>View Details
                    </a>
                </div>
            </div>
            `;
        }).join('');

        container.innerHTML = html;
    }
}

// Initialize when DOM is ready
document.addEventListener('DOMContentLoaded', () => {
    new HistoryManager();
});
