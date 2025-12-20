// --- Global ---
function closeModal() {
    document.getElementById('modal-container').classList.add('hidden');
}

function getISTDate() {
    const d = new Date();
    // distinct handling for time if needed, but input type="date" needs YYYY-MM-DD
    // IST is UTC+5:30
    const utc = d.getTime() + (d.getTimezoneOffset() * 60000);
    const titleDate = new Date(utc + (3600000 * 5.5));
    return titleDate.toISOString().split('T')[0];
}

// --- Submit Claim Page ---
// --- Utility ---
async function fetchWithTimeout(resource, options = {}) {
    const { timeout = 30000 } = options; // 30s max wait for Google Sheets
    const controller = new AbortController();
    const id = setTimeout(() => controller.abort(), timeout);
    try {
        const response = await fetch(resource, {
            ...options,
            signal: controller.signal
        });
        clearTimeout(id);
        return response;
    } catch (error) {
        clearTimeout(id);
        throw error;
    }
}

// --- Submit Claim Page ---
// Global selection state
window.selectedProducts = [];

async function searchCustomer() {
    const mobileInput = document.getElementById('mobileInput');
    const searchBtn = document.getElementById('searchBtn');
    const mobile = mobileInput.value;
    const msgBox = document.getElementById('search-msg');
    const formSection = document.getElementById('claim-form-section');

    if (!mobile || mobile.length !== 10) {
        msgBox.textContent = "Please enter a valid 10-digit number.";
        msgBox.className = "msg-box warning";
        msgBox.classList.remove('hidden');
        return;
    }

    // Show loading & Disable inputs
    msgBox.textContent = "Searching Database...";
    msgBox.className = "msg-box info";
    msgBox.classList.remove('hidden');

    // UI Feedback
    mobileInput.disabled = true;
    searchBtn.disabled = true;
    const originalBtnText = searchBtn.innerHTML;
    searchBtn.innerHTML = '<i class="ri-loader-4-line spin"></i> Searching...';

    // Reset selection
    window.selectedProducts = [];
    renderClaimForms();

    try {
        const response = await fetchWithTimeout('/lookup-customer', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ mobile: mobile })
        });

        const data = await response.json();

        msgBox.classList.add('hidden');
        formSection.classList.remove('hidden');

        if (data.success) {
            // Found existing customer
            document.getElementById('disp-name').textContent = data.customer_name;
            document.getElementById('disp-mobile').textContent = mobile;
            document.getElementById('hidden_name').value = data.customer_name;
            document.getElementById('hidden_mobile').value = mobile;

            // Populate Products
            const productList = document.getElementById('product-list');
            productList.innerHTML = "";

            if (data.products && data.products.length > 0) {
                data.products.forEach((prod, index) => {
                    const el = document.createElement('div');
                    el.className = 'product-card';
                    el.dataset.index = index; // Store index for reference
                    el.innerHTML = `
                        <h4>${prod.model}</h4>
                        <p style="font-size:0.8rem; color:#777">Serial: ${prod.serial}</p>
                        <p style="font-size:0.8rem; color:#777">OSID: ${prod.osid}</p>
                        <p style="font-size:0.8rem; color:#777">Inv: ${prod.invoice}</p>
                    `;
                    el.onclick = () => toggleProductSelection(prod, el);
                    productList.appendChild(el);
                });
            } else {
                productList.innerHTML = '<p style="color:#777; font-style:italic;">No registered products found. Register a new one below.</p>';
                // Allow manual entry for existing customer? 
                // For simplicity, fallback to manual logic if list empty?
                // Or user can use New Customer flow?
                // Let's assume list is populated.
            }

        } else {
            // New Customer
            msgBox.textContent = "New Customer! Please enter details.";
            msgBox.className = "msg-box info";
            msgBox.classList.remove('hidden');

            document.getElementById('disp-name').innerHTML = `<input type="text" id="manual_name" placeholder="Enter Name" class="manual-input" onchange="document.getElementById('hidden_name').value = this.value">`;
            document.getElementById('disp-mobile').textContent = mobile;
            document.getElementById('hidden_name').value = "";
            document.getElementById('hidden_mobile').value = mobile;
            // Render Manual Product Form (Single for now)
            // We treat it as one selected product
            const manualProd = { model: '', serial: '', invoice: '', osid: 'MANUAL_ENTRY', isManual: true };
            window.selectedProducts = [manualProd];

            document.getElementById('product-list').innerHTML = `
                <div class="manual-product-form" style="padding:1rem; background:rgba(67, 97, 238, 0.05); border-radius:12px; border:1px solid rgba(67, 97, 238, 0.2);">
                    <h4 style="margin-bottom:0.8rem; color:var(--primary);">New Product Details</h4>
                    <div class="input-group" style="display:flex; gap:0.5rem; margin-bottom:0.5rem">
                         <input type="text" class="manual-input" style="border:1px solid #ddd; padding:0.5rem; border-radius:8px;" placeholder="Model Name" onchange="updateManualProduct(this, 'model')">
                         <input type="text" class="manual-input" style="border:1px solid #ddd; padding:0.5rem; border-radius:8px;" placeholder="Serial No" onchange="updateManualProduct(this, 'serial')">
                    </div>
                    <div class="input-group">
                         <input type="text" class="manual-input" style="border:1px solid #ddd; padding:0.5rem; border-radius:8px; width:100%;" placeholder="Invoice No" onchange="updateManualProduct(this, 'invoice')">
                    </div>
                </div>
            `;

            window.updateManualProduct = function (el, field) {
                window.selectedProducts[0][field] = el.value;
                // Re-render only if needed, but here inputs are live.
                // We need to render the CLAIM FORM for this manual product immediately?
                renderClaimForms(); // To show Issue/Upload inputs
            };

            renderClaimForms();
        }
    } catch (e) {
        msgBox.textContent = "Server Timeout or Error. Please check connection.";
        msgBox.className = "msg-box error";
        msgBox.classList.remove('hidden');
        console.error(e);
    } finally {
        mobileInput.disabled = false;
        searchBtn.disabled = false;
        searchBtn.innerHTML = originalBtnText;
    }
}

// Toggle Selection
function toggleProductSelection(product, element) {
    const index = window.selectedProducts.findIndex(p => p.osid === product.osid && p.serial === product.serial);

    if (index === -1) {
        // Add
        window.selectedProducts.push(product);
        element.classList.add('selected');
    } else {
        // Remove
        window.selectedProducts.splice(index, 1);
        element.classList.remove('selected');
    }
    renderClaimForms();
}

// Render Dynamic Forms
function renderClaimForms() {
    const container = document.getElementById('dynamic-claim-forms');

    if (window.selectedProducts.length === 0) {
        container.innerHTML = `
            <div class="empty-selection-msg" style="text-align: center; color: var(--text-tertiary); padding: 2rem; border: 2px dashed #e5e7eb; border-radius: 12px;">
                <i class="ri-shopping-cart-line" style="font-size: 2rem; margin-bottom: 0.5rem; display: block;"></i>
                Please select products above to add claim details
            </div>`;
        return;
    }

    // Preserve existing input values if re-rendering? 
    // For simplicity, we might lose values if toggling. 
    // To fix, we should store values in the product object or a separate map.
    // Basic implementation: Just re-render. User should verify.

    container.innerHTML = "";

    window.selectedProducts.forEach((prod, index) => {
        const div = document.createElement('div');
        div.className = 'claim-card-dynamic';
        div.style.cssText = "background: #fff; border: 1px solid #e5e7eb; border-radius: 12px; padding: 1.5rem; margin-bottom: 1.5rem; box-shadow: 0 4px 6px -1px rgba(0,0,0,0.05);";

        div.innerHTML = `
            <h4 style="color: var(--primary); margin-bottom: 1rem; border-bottom: 1px solid #eee; padding-bottom: 0.5rem;">
                <i class="ri-smartphone-line"></i> ${prod.model || 'New Product'}
            </h4>
            
            <div class="grid-2">
                 <div class="form-group">
                    <label style="color: var(--text-tertiary); font-size: 0.8rem; font-weight:600;">Issue Description</label>
                    <textarea id="issue_${index}" rows="2" placeholder="Describe issue for this product..." required
                        style="width: 100%; padding: 0.8rem; border-radius: 8px; border: 1px solid #ddd; background: #f9fafb; outline: none;"></textarea>
                 </div>
                 <div class="form-group">
                    <label style="color: var(--text-tertiary); font-size: 0.8rem; font-weight:600;">Upload Invoice/Docs</label>
                    <input type="file" id="files_${index}" multiple
                        style="width: 100%; padding: 0.6rem; border: 1px dashed #ccc; border-radius: 8px; background: #fbfbfb;">
                    <p style="font-size:0.75rem; color:#999; margin-top:4px;">If invoice is same as another, you can upload once here.</p>
                 </div>
            </div>
        `;
        container.appendChild(div);
    });
}

// Handle Form Submit
const subForm = document.getElementById('submissionForm');
if (subForm) {
    subForm.onsubmit = async (e) => {
        e.preventDefault();

        if (window.selectedProducts.length === 0) {
            alert("Please select at least one product.");
            return;
        }

        const formData = new FormData(subForm);
        const loader = document.getElementById('loader');
        loader.classList.remove('hidden');

        // Build Claims Data
        const claimsList = window.selectedProducts.map((prod, index) => {
            const issueEl = document.getElementById(`issue_${index}`);
            return {
                ...prod,
                issue: issueEl ? issueEl.value : "No Issue Description",
                file_key: `files_${index}`
            };
        });

        formData.append('claims_data', JSON.stringify(claimsList));

        // Append Files
        window.selectedProducts.forEach((_, index) => {
            const fileInput = document.getElementById(`files_${index}`);
            if (fileInput && fileInput.files.length > 0) {
                for (let i = 0; i < fileInput.files.length; i++) {
                    formData.append(`files_${index}`, fileInput.files[i]);
                }
            }
        });

        try {
            const res = await fetchWithTimeout('/submit-claim', {
                method: 'POST',
                body: formData
            });
            const result = await res.json();

            loader.classList.add('hidden');

            if (result.success) {
                alert(result.message);
                window.location.reload();
            } else {
                alert("Error: " + result.message);
            }
        } catch (err) {
            loader.classList.add('hidden');
            console.error(err);
            if (err.name === 'AbortError') {
                alert("Submission timed out. Server busy.");
            } else {
                alert("Submission failed. Check network.");
            }
        }
    }
}


// --- Dashboard Page ---
function filterTable() {
    const input = document.getElementById("searchInput");
    const filter = input.value.toUpperCase();
    const table = document.querySelector(".premium-table");
    const tr = table.getElementsByTagName("tr");

    for (let i = 1; i < tr.length; i++) {
        let txtValue = tr[i].textContent || tr[i].innerText;
        if (txtValue.toUpperCase().indexOf(filter) > -1) {
            tr[i].style.display = "";
        } else {
            tr[i].style.display = "none";
        }
    }
}

// Modal Logic
let currentClaimId = null;

async function openClaimModal(id) {
    currentClaimId = id;

    // Feedback: Wait cursor
    document.body.style.cursor = 'wait';

    try {
        // 1. Fetch data FIRST
        const res = await fetch(`/claim/${id}`);
        if (!res.ok) throw new Error("Fetch failed");
        const data = await res.json();

        // 2. Prepare Modal (Still Hidden)
        const modal = document.getElementById('modal-container');
        const body = document.getElementById('modal-body');
        const tmpl = document.getElementById('claimDetailTemplate').content.cloneNode(true);

        // Clear previous content and append new template
        body.innerHTML = '';
        body.appendChild(tmpl);

        // 3. Populate fields
        document.getElementById('modalTitle').textContent = `Claim #${id} - ${data.customer_name}`;

        const subDate = document.getElementById('submittedDate');
        if (subDate) subDate.value = data.date || '';

        const statusSel = document.getElementById('updateStatus');
        if (statusSel) statusSel.value = data.status;

        // Populate other fields
        const settledDate = document.getElementById('settledDate');
        if (settledDate) settledDate.value = data.claim_settled_date || '';

        const followUpDate = document.getElementById('followUpDate');
        if (followUpDate) followUpDate.value = data.follow_up_date || '';

        const followUpHist = document.getElementById('followUpHistory');
        if (followUpHist) followUpHist.value = data.follow_up_notes || '';

        const newNote = document.getElementById('newFollowUpNote');
        if (newNote) newNote.value = "";

        const staff = document.getElementById('assignedStaff');
        if (staff) staff.value = data.assigned_staff || '';

        // Populate new fields
        const osidEl = document.getElementById('claimOsid');
        if (osidEl) osidEl.value = data.osid || '';

        const srNoEl = document.getElementById('claimSrNo');
        if (srNoEl) srNoEl.value = data.sr_no || '';

        // Repair Section
        const chkFb = document.getElementById('chk_repair_feedback');
        if (chkFb) chkFb.checked = data.repair_feedback_completed;

        // Initialize Workflow UI (Replacement)
        if (typeof window.initializeWorkflow === 'function') {
            window.initializeWorkflow(data);
        } else {
            // Fallback helper
            const setChk = (eid, val) => { const e = document.getElementById(eid); if (e) e.checked = val; };
            setChk('chk_repl_confirmation', data.replacement_confirmation);
            setChk('chk_repl_osg_approval', data.replacement_osg_approval);
            setChk('chk_repl_mail_store', data.replacement_mail_store);
            setChk('chk_repl_invoice_gen', data.replacement_invoice_gen);
            setChk('chk_repl_invoice_sent', data.replacement_invoice_sent);
            setChk('chk_repl_settled_accounts', data.replacement_settled_accounts);
        }

        // TAT
        const dispTat = document.getElementById('disp_tat');
        if (dispTat) dispTat.textContent = (data.tat !== null && data.tat !== undefined) ? data.tat : "--";

        // Complete Checkboxes
        const isComplete = data.complete;
        const chkRep = document.getElementById('chk_complete_repair');
        const chkRepl = document.getElementById('chk_complete_repl');
        if (chkRep) chkRep.checked = isComplete;
        if (chkRepl) chkRepl.checked = isComplete;

        // 4. Run UI Logic
        // Attach listener first so logic runs correctly
        if (statusSel) statusSel.addEventListener('change', checkStatusUI);
        checkStatusUI();

        // 5. FINALLY Show Modal
        modal.classList.remove('hidden');

    } catch (e) {
        console.error(e);
        alert("Failed to load claim details. Please try again.");
    } finally {
        // Reset cursor
        document.body.style.cursor = 'default';
    }
}

function checkStatusUI() {
    const status = document.getElementById('updateStatus').value;
    const isSubmitted = status === 'Submitted';
    const isRegistered = status === 'Registered';
    const isFollowUp = status === 'Follow Up';
    const isRepairCompleted = status === 'Repair Completed';

    // Tabs Buttons / Container
    const tabsContainer = document.querySelector('#modal-body .tabs');
    const btnWorkflow = document.getElementById('btn-tab-workflow');
    const btnNotes = document.getElementById('btn-tab-notes');

    // Sections
    const TabWorkflow = document.getElementById('tab-workflow');
    const TabNotes = document.getElementById('tab-notes');

    // Workflow Sub-Sections
    const wfSectionRepair = document.getElementById('wf-section-repair');
    const wfSectionRepl = document.getElementById('workflow-replacement-section');

    // Info Fields
    const GrpSettled = document.getElementById('grp-settled');
    const GrpStaff = document.getElementById('grp-staff');
    const GrpSubmitted = document.getElementById('grp-submitted');
    const GrpOsid = document.getElementById('grp-osid');
    const GrpSrNo = document.getElementById('grp-srno');
    const wfSectionFollowUp = document.getElementById('wf-section-followup');

    // Controls
    const btnSave = document.getElementById('btn-save-changes');
    const subDateInput = document.getElementById('submittedDate');

    // --- Modes ---

    if (isSubmitted || isRegistered) {
        // Mode 1: Info Only (Date only)
        if (tabsContainer) tabsContainer.classList.add('hidden');

        switchTab('info');

        // Hide other tabs content explicitly
        if (TabWorkflow) TabWorkflow.classList.add('hidden');
        if (TabNotes) TabNotes.classList.add('hidden');

        // Layout Info Fields
        if (GrpSettled) GrpSettled.classList.add('hidden');
        if (GrpStaff) GrpStaff.classList.add('hidden');
        if (GrpSubmitted) GrpSubmitted.classList.remove('hidden');

        // Ensure SR No/OSID visible
        if (GrpOsid) GrpOsid.classList.remove('hidden');
        if (GrpSrNo) GrpSrNo.classList.remove('hidden');

        // Controls
        if (isRegistered) {
            // Registered: Set Date to Today (IST), Readonly, Show Save
            if (btnSave) btnSave.classList.remove('hidden');
            if (subDateInput) {
                subDateInput.value = getISTDate();
                subDateInput.setAttribute('readonly', true);
            }
        } else {
            // Submitted: Readonly Date (Historical), Hide Save
            if (btnSave) btnSave.classList.add('hidden');
            if (subDateInput) subDateInput.setAttribute('readonly', true);
        }

    } else if (isFollowUp || status === 'Closed') {
        // Mode 2: Follow Up OR Closed (Now inside Workflow section)
        if (tabsContainer) tabsContainer.classList.add('hidden');

        switchTab('workflow'); // Force Workflow Tab instead of Notes

        // Ensure Visibility of Workflow Tab Only
        if (TabWorkflow) TabWorkflow.classList.remove('hidden');
        if (TabNotes) TabNotes.classList.add('hidden');

        // Toggle Subsections: Only show Follow Up history
        if (wfSectionRepair) wfSectionRepair.classList.add('hidden');
        if (wfSectionRepl) wfSectionRepl.classList.add('hidden');
        if (wfSectionFollowUp) wfSectionFollowUp.classList.remove('hidden');

        // Controls
        if (btnSave) btnSave.classList.remove('hidden');

        // Follow Up Date: Today (IST), Readonly
        const followUpDateInput = document.getElementById('followUpDate');
        if (followUpDateInput) {
            followUpDateInput.value = getISTDate();
            followUpDateInput.setAttribute('readonly', true);
        }

        // Safe reset
        if (subDateInput) subDateInput.setAttribute('readonly', true);

    } else if (isRepairCompleted) {
        // Mode 3: Repair Completed (Workflow -> Repair Only)
        if (tabsContainer) tabsContainer.classList.add('hidden');

        switchTab('workflow'); // Force Workflow Tab

        // Ensure Visibility of Workflow Tab Only
        if (TabWorkflow) TabWorkflow.classList.remove('hidden');
        if (TabNotes) TabNotes.classList.add('hidden');

        // Toggle Subsections
        if (wfSectionRepair) wfSectionRepair.classList.remove('hidden');
        if (wfSectionRepl) wfSectionRepl.classList.add('hidden');
        if (wfSectionFollowUp) wfSectionFollowUp.classList.add('hidden'); // Hide follow up here

        // Controls
        if (btnSave) btnSave.classList.remove('hidden');
        if (subDateInput) subDateInput.setAttribute('readonly', true);

    } else if (status === 'Replacement Approved' || status === 'Replacement approved') {
        // Mode 4: Replacement Approved (Workflow -> Replacement Only)
        if (tabsContainer) tabsContainer.classList.add('hidden');

        switchTab('workflow'); // Force Workflow Tab

        // Ensure Visibility of Workflow Tab Only
        if (TabWorkflow) TabWorkflow.classList.remove('hidden');
        if (TabNotes) TabNotes.classList.add('hidden');

        // Toggle Subsections: HIDE Repair, SHOW Replacement
        if (wfSectionRepair) wfSectionRepair.classList.add('hidden');
        if (wfSectionRepl) wfSectionRepl.classList.remove('hidden');

        // Controls
        if (btnSave) btnSave.classList.remove('hidden');
        if (subDateInput) subDateInput.setAttribute('readonly', true);

    } else {
        // Mode 5: Full Workflow / Other
        if (tabsContainer) tabsContainer.classList.remove('hidden');

        // Show all Buttons
        if (btnWorkflow) btnWorkflow.classList.remove('hidden');
        if (btnNotes) btnNotes.classList.remove('hidden');

        // Ensure content not forced hidden
        if (TabWorkflow) TabWorkflow.classList.remove('hidden');
        if (TabNotes) TabNotes.classList.remove('hidden');

        // Show all Workflow Subsections
        if (wfSectionRepair) wfSectionRepair.classList.remove('hidden');
        if (wfSectionRepl) wfSectionRepl.classList.remove('hidden');

        // Restore Info Fields
        if (GrpSettled) GrpSettled.classList.remove('hidden');
        if (GrpStaff) GrpStaff.classList.remove('hidden');
        if (GrpSubmitted) GrpSubmitted.classList.remove('hidden');

        // Controls
        if (btnSave) btnSave.classList.remove('hidden');
        if (subDateInput) subDateInput.setAttribute('readonly', true);
    }
}

// Rewrite switchTab correctly
window.switchTab = function (tabName) {
    const modalBody = document.getElementById('modal-body'); // Scope to modal
    const buttons = modalBody.querySelectorAll('.tab-btn');
    const contents = modalBody.querySelectorAll('.tab-content');

    buttons.forEach(btn => {
        if (btn.textContent.toLowerCase().includes(tabName.replace('tab-', '')))
            btn.classList.add('active'); // Dirty heuristic, but simpler is:
        else btn.classList.remove('active');
    });

    contents.forEach(c => c.classList.remove('active'));
    const target = modalBody.querySelector(`#tab-${tabName}`);
    if (target) target.classList.add('active');

    // Highlight button
    // We can assume the order Info(0), Workflow(1), Notes(2)
    buttons.forEach(b => b.classList.remove('active'));
    if (tabName === 'info') buttons[0].classList.add('active');
    if (tabName === 'workflow') buttons[1].classList.add('active');
    if (tabName === 'notes') buttons[2].classList.add('active');
}

async function saveClaimChanges() {
    // History handling
    const oldHistory = document.getElementById('followUpHistory').value;
    const newNote = document.getElementById('newFollowUpNote').value.trim();
    let combinedNotes = oldHistory;
    let newRemarks = ""; // Default if no note

    if (newNote) {
        // Append new note with timestamp
        const timestamp = new Date().toLocaleString('en-IN');
        combinedNotes = (oldHistory ? oldHistory + "\n" : "") + `[${timestamp}] ${newNote}`;
        // Remarks is just the latest note
        newRemarks = newNote;
    }

    const payload = {
        status: document.getElementById('updateStatus').value,
        date: document.getElementById('submittedDate').value,
        follow_up_date: document.getElementById('followUpDate').value || null,

        // Use the combined history for "Follow Up - Notes" column
        follow_up_notes: combinedNotes,
        assigned_staff: (document.getElementById('assignedStaff')?.value || '').trim(),
        sr_no: (document.getElementById('claimSrNo')?.value || '').trim(),
    };

    if (newNote) {
        payload.remarks = newRemarks;
    }

    // Determine values from duplicated checkboxes
    const fb1 = document.getElementById('chk_repair_feedback').checked;
    const isFeedbackDone = fb1;

    const cmp1 = document.getElementById('chk_complete_repair') ? document.getElementById('chk_complete_repair').checked : false;
    const cmp2 = document.getElementById('chk_complete_repl') ? document.getElementById('chk_complete_repl').checked : false;
    let isComplete = cmp1 || cmp2;

    // Auto-mark as complete if status is Closed
    if (payload.status === 'Closed') {
        isComplete = true;
    }

    // Replacement Workflow Checkboxes (Columns O-T)
    const getReplCheckbox = (id) => {
        const el = document.getElementById(id);
        return el ? el.checked : false;
    };

    // Other fields
    payload.assigned_staff = document.getElementById('assignedStaff').value;
    payload.repair_feedback_completed = isFeedbackDone;

    // Replacement workflow fields (Columns O-T)
    payload.replacement_confirmation = getReplCheckbox('chk_repl_confirmation');
    payload.replacement_osg_approval = getReplCheckbox('chk_repl_osg_approval');
    payload.replacement_mail_store = getReplCheckbox('chk_repl_mail_store');
    payload.replacement_invoice_gen = getReplCheckbox('chk_repl_invoice_gen');
    payload.replacement_invoice_sent = getReplCheckbox('chk_repl_invoice_sent');
    payload.replacement_settled_accounts = getReplCheckbox('chk_repl_settled_accounts');

    // Complete flag (Column U)
    payload.complete = isComplete;

    try {
        const res = await fetch(`/update-claim/${currentClaimId}`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(payload)
        });
        const d = await res.json();
        if (d.success) {
            closeModal();
            alert("Changes saved successfully!");
            window.location.reload();
        } else {
            alert("Failed to update: " + (d.message || "Unknown error"));
        }
    } catch (e) {
        alert("Error updating");
    }
}

// Date Display
const d = new Date();
const dateStr = d.toLocaleDateString('en-IN', { weekday: 'long', year: 'numeric', month: 'long', day: 'numeric' });
const dateEl = document.getElementById('currentDate');
if (dateEl) dateEl.textContent = dateStr;
