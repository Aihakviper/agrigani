/**
 * AgriGani Diagnosis Detail Page
 */

class DiagnosisDetailManager {
    constructor() {
        this.container = document.getElementById('detailContainer');
        this.loading = document.getElementById('loadingSpinner');
        this.errorState = document.getElementById('errorState');
        this.init();
    }

    async init() {
        const params = new URLSearchParams(window.location.search);
        const diagnosisId = params.get('id');

        if (!diagnosisId) {
            this.showError('No diagnosis selected.');
            return;
        }

        try {
            const data = await Utils.apiRequest(`${API_CONFIG.getEndpoint('DIAGNOSES')}${diagnosisId}/`);
            this.render(data);
        } catch (error) {
            this.showError('Unable to load this diagnosis.');
        }
    }

    showError(message) {
        this.loading.style.display = 'none';
        this.container.style.display = 'none';
        this.errorState.style.display = 'block';
        this.errorState.querySelector('p').textContent = message;
    }

    render(data) {
        const disease = data.disease_details || {};
        const confidence = Number(data.confidence_score || 0);
        const vendors = data.recommended_vendors || [];

        this.loading.style.display = 'none';
        this.errorState.style.display = 'none';
        this.container.style.display = 'block';

        this.container.innerHTML = `
            <div class="result-card">
                <div class="result-header">
                    <h2 class="result-disease-name">${disease.name || data.disease_name || 'Unknown Disease'}</h2>
                    <div class="confidence-badge ${Utils.getConfidenceClass(confidence)}">
                        ${confidence.toFixed(1)}% ${Utils.getConfidenceText(confidence)}
                    </div>
                </div>

                <div class="result-body">
                    <div class="row g-4 mb-4">
                        <div class="col-lg-5">
                            ${data.image_url ? `
                                <img src="${data.image_url}" alt="Diagnosis upload" class="img-fluid rounded-3 shadow-sm">
                            ` : `
                                <div class="alert alert-info mb-0">No image is attached to this diagnosis.</div>
                            `}
                        </div>
                        <div class="col-lg-7">
                            <div class="result-section mb-0">
                                <h3 class="result-section-title">
                                    <i class="bi bi-clipboard2-pulse"></i> Diagnosis Summary
                                </h3>
                                <p><strong>Farmer:</strong> ${data.farmer_name || 'Unknown'}</p>
                                <p><strong>Location:</strong> ${data.location || 'Not provided'}</p>
                                <p><strong>Region:</strong> ${data.region_code || 'Not provided'}</p>
                                <p><strong>Model:</strong> ${data.ml_model_version || 'v1.0'}</p>
                                <p><strong>Date:</strong> ${Utils.formatDate(data.created_at)}</p>
                                ${data.notes ? `<p><strong>Notes:</strong> ${data.notes}</p>` : ''}
                            </div>
                        </div>
                    </div>

                    <div class="result-section">
                        <h3 class="result-section-title">
                            <i class="bi bi-info-circle-fill"></i> Disease Information
                        </h3>
                        <p>${disease.description || 'No disease description is available yet.'}</p>
                        ${disease.symptoms ? `<p><strong>Symptoms:</strong> ${disease.symptoms}</p>` : ''}
                        ${disease.causes ? `<p><strong>Causes:</strong> ${disease.causes}</p>` : ''}
                        ${disease.prevention_tips ? `<p><strong>Prevention:</strong> ${disease.prevention_tips}</p>` : ''}
                    </div>

                    <div class="result-section">
                        <h3 class="result-section-title">
                            <i class="bi bi-prescription2"></i> Treatment Recommendations
                        </h3>
                        ${disease.treatments && disease.treatments.length ? disease.treatments.map(treatment => `
                            <div class="treatment-card">
                                <div class="treatment-title">${treatment.medicine_name}</div>
                                <div class="treatment-detail"><strong>Dosage:</strong><span>${treatment.dosage}</span></div>
                                <div class="treatment-detail"><strong>Application:</strong><span>${treatment.application_method}</span></div>
                                <div class="treatment-detail"><strong>Frequency:</strong><span>${treatment.frequency}</span></div>
                                ${treatment.duration ? `<div class="treatment-detail"><strong>Duration:</strong><span>${treatment.duration}</span></div>` : ''}
                                ${treatment.precautions ? `<div class="alert alert-warning mt-3 mb-0">${treatment.precautions}</div>` : ''}
                            </div>
                        `).join('') : '<p class="text-muted">No treatment record is available yet.</p>'}
                    </div>

                    <div class="result-section">
                        <h3 class="result-section-title">
                            <i class="bi bi-shop"></i> Recommended Vendors
                        </h3>
                        ${vendors.length ? vendors.map(item => {
                            const vendor = item.vendor;
                            return `
                                <div class="vendor-card">
                                    <div class="vendor-name">${vendor.name}</div>
                                    <div class="vendor-type">${Utils.formatVendorType(vendor.vendor_type)}</div>
                                    <div class="vendor-info">
                                        <div><i class="bi bi-geo-alt-fill"></i><span>${vendor.location}</span></div>
                                        <div><i class="bi bi-telephone-fill"></i><a href="tel:${vendor.phone_number}">${vendor.phone_number}</a></div>
                                        ${vendor.email ? `<div><i class="bi bi-envelope-fill"></i><a href="mailto:${vendor.email}">${vendor.email}</a></div>` : ''}
                                    </div>
                                </div>
                            `;
                        }).join('') : '<p class="text-muted">No verified vendor was matched for this region.</p>'}
                    </div>

                    <div class="text-center">
                        <a href="history.html" class="btn btn-outline-primary me-2">
                            <i class="bi bi-arrow-left me-2"></i>Back to History
                        </a>
                        <a href="diagnose.html" class="btn btn-primary">
                            <i class="bi bi-camera-fill me-2"></i>New Diagnosis
                        </a>
                    </div>
                </div>
            </div>
        `;
    }
}

document.addEventListener('DOMContentLoaded', () => {
    new DiagnosisDetailManager();
});
