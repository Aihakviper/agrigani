/**
 * AgriGani Diagnosis Page
 * Main functionality for disease diagnosis
 */

class DiagnosisManager {
    constructor() {
        this.selectedFarmerId = null;
        this.selectedImage = null;
        this.farmers = [];
        
        this.init();
    }

    init() {
        this.loadFarmers();
        this.setupEventListeners();
    }

    setupEventListeners() {
        // Image upload
        const imageInput = document.getElementById('imageInput');
        const uploadArea = document.getElementById('uploadArea');
        const removeImageBtn = document.getElementById('removeImage');
        const submitBtn = document.getElementById('submitDiagnosis');
        const farmerSelect = document.getElementById('farmerSelect');

        // File input change
        imageInput.addEventListener('change', (e) => this.handleImageSelect(e.target.files[0]));

        // Drag and drop
        uploadArea.addEventListener('dragover', (e) => {
            e.preventDefault();
            uploadArea.classList.add('dragover');
        });

        uploadArea.addEventListener('dragleave', () => {
            uploadArea.classList.remove('dragover');
        });

        uploadArea.addEventListener('drop', (e) => {
            e.preventDefault();
            uploadArea.classList.remove('dragover');
            const file = e.dataTransfer.files[0];
            if (file) this.handleImageSelect(file);
        });

        // Remove image
        removeImageBtn.addEventListener('click', () => this.removeImage());

        // Farmer selection
        farmerSelect.addEventListener('change', (e) => {
            this.selectedFarmerId = e.target.value;
            this.updateSubmitButton();
        });

        // Submit diagnosis
        submitBtn.addEventListener('click', () => this.submitDiagnosis());

        // New farmer modal
        document.getElementById('saveFarmer').addEventListener('click', () => this.saveFarmer());
    }

    async loadFarmers() {
        try {
            const farmers = await Utils.apiRequest(API_CONFIG.getEndpoint('FARMERS'));
            this.farmers = farmers.results || farmers;
            this.populateFarmerSelect();
        } catch (error) {
            console.error('Error loading farmers:', error);
            Utils.showToast('Error loading farmers', 'danger');
        }
    }

    populateFarmerSelect() {
        const select = document.getElementById('farmerSelect');
        select.innerHTML = '<option value="">-- Select Farmer --</option>';
        
        this.farmers.forEach(farmer => {
            const option = document.createElement('option');
            option.value = farmer.id;
            option.textContent = `${farmer.full_name} (${farmer.phone_number})`;
            select.appendChild(option);
        });
    }

    handleImageSelect(file) {
        if (!file) return;

        try {
            // Validate image
            Utils.validateImage(file);
            
            // Store file
            this.selectedImage = file;

            // Show preview
            const reader = new FileReader();
            reader.onload = (e) => {
                document.getElementById('imagePreview').src = e.target.result;
                document.getElementById('uploadArea').querySelector('.upload-content').style.display = 'none';
                document.getElementById('previewArea').style.display = 'block';
                
                // Show image info
                const info = `${file.name} (${Utils.formatFileSize(file.size)})`;
                document.getElementById('imageInfo').textContent = info;
            };
            reader.readAsDataURL(file);

            this.updateSubmitButton();
        } catch (error) {
            Utils.showToast(error.message, 'danger');
        }
    }

    removeImage() {
        this.selectedImage = null;
        document.getElementById('imageInput').value = '';
        document.getElementById('uploadArea').querySelector('.upload-content').style.display = 'block';
        document.getElementById('previewArea').style.display = 'none';
        this.updateSubmitButton();
    }

    updateSubmitButton() {
        const submitBtn = document.getElementById('submitDiagnosis');
        submitBtn.disabled = !(this.selectedFarmerId && this.selectedImage);
    }

    async saveFarmer() {
        const form = document.getElementById('newFarmerForm');
        
        if (!form.checkValidity()) {
            form.reportValidity();
            return;
        }

        const farmerData = {
            full_name: document.getElementById('farmerName').value,
            phone_number: document.getElementById('farmerPhone').value,
            email: document.getElementById('farmerEmail').value,
            location: document.getElementById('farmerLocation').value,
            region_code: document.getElementById('farmerRegion').value,
            gender: document.getElementById('farmerGender').value,
            farm_size_hectares: document.getElementById('farmerFarmSize').value || null
        };

        try {
            const newFarmer = await Utils.apiRequest(
                API_CONFIG.getEndpoint('FARMERS'),
                {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify(farmerData)
                }
            );

            Utils.showToast('Farmer added successfully!', 'success');
            
            // Close modal
            const modal = bootstrap.Modal.getInstance(document.getElementById('newFarmerModal'));
            modal.hide();
            
            // Reset form
            form.reset();
            
            // Reload farmers and select new one
            await this.loadFarmers();
            document.getElementById('farmerSelect').value = newFarmer.id;
            this.selectedFarmerId = newFarmer.id;
            this.updateSubmitButton();
        } catch (error) {
            Utils.showToast('Error adding farmer: ' + error.message, 'danger');
        }
    }

    async submitDiagnosis() {
        if (!this.selectedFarmerId || !this.selectedImage) {
            Utils.showToast('Please select a farmer and upload an image', 'warning');
            return;
        }

        // Prepare form data
        const formData = new FormData();
        formData.append('farmer_id', this.selectedFarmerId);
        formData.append('image', this.selectedImage);
        
        const location = document.getElementById('locationInput').value;
        const regionCode = document.getElementById('regionInput').value;
        const notes = document.getElementById('notesInput').value;
        
        if (location) formData.append('location', location);
        if (regionCode) formData.append('region_code', regionCode);
        if (notes) formData.append('notes', notes);

        // Show loading
        document.getElementById('loadingContainer').style.display = 'block';
        document.getElementById('submitDiagnosis').disabled = true;

        try {
            const result = await Utils.apiRequest(
                API_CONFIG.getEndpoint('DIAGNOSES'),
                {
                    method: 'POST',
                    body: formData
                }
            );

            // Hide loading
            document.getElementById('loadingContainer').style.display = 'none';
            
            // Display results
            this.displayResults(result);
            
            Utils.showToast('Diagnosis completed successfully!', 'success');
            
            // Scroll to results
            document.getElementById('resultsContainer').scrollIntoView({ behavior: 'smooth' });
        } catch (error) {
            document.getElementById('loadingContainer').style.display = 'none';
            document.getElementById('submitDiagnosis').disabled = false;
            Utils.showToast('Error during diagnosis: ' + error.message, 'danger');
        }
    }

    displayResults(data) {
        const container = document.getElementById('resultsContainer');
        const disease = data.disease_details;
        const confidence = Number(data.confidence_score || 0);
        const vendors = data.recommended_vendors || [];

        let html = `
            <div class="result-card">
                <div class="result-header">
                    <h2 class="result-disease-name">${disease.name}</h2>
                    <div class="confidence-badge ${Utils.getConfidenceClass(confidence)}">
                        ${confidence.toFixed(1)}% ${Utils.getConfidenceText(confidence)}
                    </div>
                </div>
                
                <div class="result-body">
                    <!-- Disease Information -->
                    <div class="result-section">
                        <h3 class="result-section-title">
                            <i class="bi bi-info-circle-fill"></i> Disease Information
                        </h3>
                        <div class="mb-3">
                            <strong>Category:</strong> ${disease.category}
                        </div>
                        <div class="mb-3">
                            <strong>Description:</strong><br>
                            ${disease.description}
                        </div>
                        <div class="mb-3">
                            <strong>Symptoms:</strong><br>
                            ${disease.symptoms}
                        </div>
                        ${disease.causes ? `
                        <div class="mb-3">
                            <strong>Causes:</strong><br>
                            ${disease.causes}
                        </div>
                        ` : ''}
                        ${disease.prevention_tips ? `
                        <div class="mb-3">
                            <strong>Prevention:</strong><br>
                            ${disease.prevention_tips}
                        </div>
                        ` : ''}
                        <div>
                            <strong>Severity:</strong> ${Utils.getSeverityBadge(disease.severity_level)}
                        </div>
                    </div>

                    <!-- Treatment Recommendations -->
                    <div class="result-section">
                        <h3 class="result-section-title">
                            <i class="bi bi-prescription2"></i> Treatment Recommendations
                        </h3>
                        ${disease.treatments && disease.treatments.length > 0 ? 
                            disease.treatments.map(treatment => `
                                <div class="treatment-card">
                                    <div class="treatment-title">${treatment.medicine_name}</div>
                                    ${treatment.active_ingredient ? `
                                        <div class="treatment-detail">
                                            <strong>Active Ingredient:</strong>
                                            <span>${treatment.active_ingredient}</span>
                                        </div>
                                    ` : ''}
                                    <div class="treatment-detail">
                                        <strong>Dosage:</strong>
                                        <span>${treatment.dosage}</span>
                                    </div>
                                    <div class="treatment-detail">
                                        <strong>Application:</strong>
                                        <span>${treatment.application_method}</span>
                                    </div>
                                    <div class="treatment-detail">
                                        <strong>Frequency:</strong>
                                        <span>${treatment.frequency}</span>
                                    </div>
                                    ${treatment.duration ? `
                                        <div class="treatment-detail">
                                            <strong>Duration:</strong>
                                            <span>${treatment.duration}</span>
                                        </div>
                                    ` : ''}
                                    ${treatment.precautions ? `
                                        <div class="alert alert-warning mt-3 mb-0">
                                            <i class="bi bi-exclamation-triangle-fill me-2"></i>
                                            <strong>Precautions:</strong> ${treatment.precautions}
                                        </div>
                                    ` : ''}
                                </div>
                            `).join('')
                            : '<p class="text-muted">No specific treatment information available. Please consult an agricultural expert.</p>'
                        }
                    </div>

                    <!-- Recommended Vendors -->
                    ${vendors.length > 0 ? `
                        <div class="result-section">
                            <h3 class="result-section-title">
                                <i class="bi bi-shop"></i> Recommended Vendors
                            </h3>
                            <p class="text-muted mb-3">Contact these verified vendors to purchase the recommended treatments:</p>
                            ${vendors.map(item => {
                                const vendor = item.vendor;
                                return `
                                    <div class="vendor-card">
                                        <div class="vendor-name">${vendor.name}</div>
                                        <div class="vendor-type">${Utils.formatVendorType(vendor.vendor_type)}</div>
                                        ${vendor.is_verified ? '<span class="badge bg-success mb-2"><i class="bi bi-patch-check-fill me-1"></i>Verified</span>' : ''}
                                        <div class="vendor-info">
                                            <div>
                                                <i class="bi bi-geo-alt-fill"></i>
                                                <span>${vendor.location}</span>
                                            </div>
                                            <div>
                                                <i class="bi bi-telephone-fill"></i>
                                                <a href="tel:${vendor.phone_number}">${vendor.phone_number}</a>
                                            </div>
                                            ${vendor.email ? `
                                                <div>
                                                    <i class="bi bi-envelope-fill"></i>
                                                    <a href="mailto:${vendor.email}">${vendor.email}</a>
                                                </div>
                                            ` : ''}
                                            ${vendor.rating ? `
                                                <div class="vendor-rating">
                                                    <i class="bi bi-star-fill"></i>
                                                <span>${Number(vendor.rating).toFixed(1)}</span>
                                                </div>
                                            ` : ''}
                                        </div>
                                    </div>
                                `;
                            }).join('')}
                        </div>
                    ` : ''}

                    <!-- Action Buttons -->
                    <div class="text-center mt-4">
                        <a href="diagnose.html" class="btn btn-primary me-2">
                            <i class="bi bi-arrow-repeat me-2"></i>New Diagnosis
                        </a>
                        <a href="history.html" class="btn btn-outline-primary">
                            <i class="bi bi-clock-history me-2"></i>View History
                        </a>
                    </div>
                </div>
            </div>
        `;

        container.innerHTML = html;
        container.style.display = 'block';
    }
}

// Initialize when DOM is ready
document.addEventListener('DOMContentLoaded', () => {
    new DiagnosisManager();
});
