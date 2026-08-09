const yourname = document.getElementById("your-name");
const username = document.getElementById("username");

let userdata;

// API
const whoami = "/api/auth/whoami";
const accountDeletionAPI = "/api/account/delete";

// Dialog
const dialogElm = document.getElementById("edit-account-modal");
const dialogForm = document.getElementById("edit_account_form");
const progressIndicator = document.querySelector(".button-progress-indicator");

const showPasswordContainer = document.getElementById(
    "show_password_container",
);

// ========== Biodata ==========
// Form dialog
async function formDialog(name, headline, label, type) {
    dialogElm.querySelector('[slot="headline"]').innerText = headline;

    // Set the form field
    dialogForm.edit_account.name = name;
    dialogForm.edit_account.placeholder = label;
    dialogForm.edit_account.type = type;

    // For password
    if (name === "password") {
        // Set value of field
        dialogForm.edit_account.value = "";

        // Enable required element
        dialogForm.retype_password.classList.remove("hidden");
        showPasswordContainer.classList.remove("hidden");
        dialogForm.retype_password.disabled = false;
        dialogForm.show_password.disabled = false;
    } else {
        // Set value of field
        dialogForm.edit_account.value =
            name === "name" ? userdata.name : userdata.username;

        // Disable unecessary element
        dialogForm.retype_password.classList.add("hidden");
        showPasswordContainer.classList.add("hidden");
        dialogForm.retype_password.disabled = true;
        dialogForm.show_password.disabled = true;
    }

    // Show the dialog
    loadRequired();
    await dialogElm.show();
}

async function closeDialog() {
    dialogForm.reset();
    await dialogElm.close();
}

// Reset everything on dialog if closed
dialogElm.addEventListener("close", () => {
    dialogForm.save_changes.disabled = true;
    hideSupportText(dialogForm.edit_account);
    hideSupportText(dialogForm.retype_password);
});

// Dialog action button
dialogForm.addEventListener("submit", (event) => {
    event.preventDefault();

    if (progressIndicator.classList.contains("hidden!")) {
        progressIndicator.classList.remove("hidden!");

        changeBio(dialogForm);
    }
});
dialogElm.onreset = closeDialog;

// Change bio
async function changeBio(theForm) {
    const available = await checkSession();
    if (available) {
        try {
            let formData = new FormData(theForm);

            // Set the route based on what name field is.
            let accountUpdateAPI = "/api/account/update";
            let requestMethod = "PATCH";

            if (theForm.edit_account.name === "password") {
                accountUpdateAPI = "/api/account/change-password";
                requestMethod = "PUT";

                // Check the password
                if (
                    dialogForm.edit_account.value !==
                    dialogForm.retype_password.value
                ) {
                    progressIndicator.classList.add("hidden!");
                    showSupportText(
                        dialogForm.retype_password,
                        "The password does not match. Please try again.",
                    );
                    return;
                }
            }

            formData = Object.fromEntries(formData.entries());

            // Send request
            const result = await sendRequest(
                accountUpdateAPI,
                formData,
                requestMethod,
            );

            if (result.code === 200) {
                // Reload user data
                const reload = await loadUserData();

                if (reload) {
                    yourname.textContent = userdata.name;
                    username.textContent = userdata.username;
                }

                progressIndicator.classList.add("hidden!");
                dialogForm.save_changes.disabled = true;

                closeDialog();
                showSnackbar(result.message);
            }
        } catch (error) {
            progressIndicator.classList.add("hidden!");

            if (error.code && error.code !== 500) {
                showSupportText(dialogForm.edit_account, error.message);
            }
        }
    } else {
        progressIndicator.classList.add("hidden!");
        showAlert(
            "Unable to edit profile information",
            "Your session has expired. Please log in again.",
        );
    }
}

// ========== Import option ==========
const browseBtn = document.getElementById("browse-btn");
const fileInput = document.getElementById("file_input");
const dropZone = document.getElementById("drop-zone");
const fileInfo = document.getElementById("file-info");
const fileNameSpan = document.getElementById("file-name");
const clearFileBtn = document.getElementById("clear-file-btn");
const importBtn = document.getElementById("submit_import_btn");
const importBtnIndicator = importBtn.querySelector(
    ".button-progress-indicator",
);
const importManifestHead = document.getElementById("import-manifest-heading");
const importManifestDesc = document.getElementById("import-manifest-desc");

const importDialog = document.getElementById("import-dialog");
const importForm = document.getElementById("import_form");

// Trigger the dialog
async function openImportMenu() {
    await importDialog.show();
}
async function closeImportMenu() {
    await importDialog.close();

    importForm.reset();
    importForm.file_password.setAttribute("type", "password");
    resetFileState();
}

// Field visibility
function showPwField() {
    importForm.file_password.setAttribute("required", true);
    importForm.file_password.disabled = false;
    importForm.file_password.parentElement.classList.remove("hidden");
}
function hidePwField() {
    importForm.file_password.removeAttribute("required");
    importForm.file_password.disabled = true;
    importForm.file_password.parentElement.classList.add("hidden");
}

function showKeySelector() {
    importForm.select_key.setAttribute("required", true);
    importForm.select_key.disabled = false;
    importForm.select_key.parentElement.classList.remove("hidden");
}
function hideKeySelector() {
    importForm.select_key.removeAttribute("required");
    importForm.select_key.disabled = true;
    importForm.select_key.parentElement.classList.add("hidden");
}

// Show file card, hide drop zone
function showFileState(file) {
    if (!file) return;

    // Read the file
    const reader = new FileReader();

    reader.onload = (e) => {
        const fileContent = e.target.result.trim();
        const extension = file.name.split(".").pop().toLowerCase();
        let isEncrypted = false;

        if (extension === "json") {
            // Import manifest status
            importManifestHead.textContent = "Valid Native Backup Detected";
            importManifestDesc.textContent =
                "Ready to parse application structural archive. This will merge existing keys and entries safely with the backup data.";

            // Hide key selector if visible
            hideKeySelector();

            // Check the file
            try {
                const parseData = JSON.parse(fileContent);
                const encryptStatus = parseData.metadata.encrypted;

                if (encryptStatus) {
                    showPwField();
                } else {
                    hidePwField();
                }
            } catch (err) {
                resetFileState();
                showAlert(
                    "Unable to read metadata",
                    "The file you selected is corrupt or unsupported. Make sure the file you selected is not corrupted and comes from the Sunako.",
                );
            }
        } else {
            // Import manifest status
            importManifestHead.textContent =
                "Compatibility Spreadsheet Detected";
            importManifestDesc.textContent =
                "Ready to parse a plaintext password manifest. This will append external records to your current data ledger.";

            showKeySelector();
        }
    };

    reader.readAsText(file);

    // Display the file name
    fileNameSpan.textContent = file.name;
    dropZone.style.display = "none";
    fileInfo.style.display = "flex";
    importBtn.disabled = false;
}

// Reset back to upload drop zone state
function resetFileState() {
    fileInput.value = ""; // Clear file buffer
    fileInfo.style.display = "none";
    dropZone.style.display = "flex";

    importManifestHead.textContent = "Awaiting File Selection";
    importManifestDesc.textContent =
        "Please select a valid archive. Native backups (.json) will restore both your keys and passwords, while standard spreadsheets (.csv) will append browser passwords.";

    hidePwField();
    hideKeySelector();

    hideSupportText(importForm.file_password);

    importBtn.disabled = true;
}

// Native trigger
browseBtn.addEventListener("click", () => fileInput.click());

fileInput.addEventListener("change", (e) => {
    if (e.target.files.length > 0) {
        showFileState(e.target.files[0]);
    }
});

// Clear selection click event
clearFileBtn.addEventListener("click", resetFileState);

// Drag-and-drop handles
dropZone.addEventListener("dragover", (e) => {
    e.preventDefault();
    dropZone.classList.add("drag-over");
});

dropZone.addEventListener("dragleave", () => {
    dropZone.classList.remove("drag-over");
});

dropZone.addEventListener("drop", (e) => {
    e.preventDefault();
    dropZone.classList.remove("drag-over");

    if (e.dataTransfer.files.length > 0) {
        const droppedFile = e.dataTransfer.files[0];
        const extension = droppedFile.name.split(".").pop().toLowerCase();

        if (extension === "json" || extension === "csv") {
            fileInput.files = e.dataTransfer.files;
            showFileState(droppedFile);
        } else {
            showAlert(
                "Unsupported file format",
                "The selected file could not be recognized. Please upload a valid backup file with a .json or .csv extension.",
            );
        }
    }
});

// Trigger Import
async function importData(theForm) {
    const available = await checkSession();
    if (available) {
        const theFile = theForm.file_input.files[0];
        const importAPI = "/api/account/import";

        const formData = new FormData(theForm);
        const payload = Object.fromEntries(formData.entries());
        const readerFile = new FileReader();

        // List of supported file type
        let itsCsvFile =
            theFile.name.endsWith(".csv") && theFile.type === "text/csv";

        let itsJsonFile =
            theFile.name.endsWith(".json") &&
            theFile.type === "application/json";

        // Check file type, then proceed to import
        readerFile.onload = (e) => {
            if (itsCsvFile) {
                // If it was .csv
                const csvContent = e.target.result;
                payload.data_sheet = csvContent;
                payload.type_file = "csv";

                sendRequest(importAPI, payload, "POST")
                    .then((response) => {
                        showSnackbar(response.message, {
                            title: "View",
                            action: "movePage('/pages/password_manager')",
                        });

                        importBtnIndicator.classList.add("hidden!");
                        closeImportMenu();
                    })
                    .catch((error) => {
                        showAlert("Unable to import data", error.message);

                        importBtnIndicator.classList.add("hidden!");
                    });
            } else if (itsJsonFile) {
                // If it was .json
                try {
                    const jsonObject = JSON.parse(e.target.result);
                    payload.json_data = jsonObject;
                    payload.type_file = "json";

                    sendRequest(importAPI, payload, "POST")
                        .then((response) => {
                            showSnackbar(response.message, {
                                title: "View",
                                action: "movePage('/pages/password_manager')",
                            });

                            importBtnIndicator.classList.add("hidden!");
                            closeImportMenu();
                        })
                        .catch((error) => {
                            if (error.code === 403) {
                                showSupportText(
                                    importForm.file_password,
                                    error.message,
                                );
                            } else {
                                showAlert(
                                    "Unable to import data",
                                    error.message,
                                );
                            }

                            importBtnIndicator.classList.add("hidden!");
                        });
                } catch (err) {
                    showAlert(
                        "Unable to import data",
                        `The selected file is corrupted or unsupported. Ensure the file is not corrupted and comes from Sunako. \nError: ${err}`,
                    );

                    importBtnIndicator.classList.add("hidden!");
                }
            } else {
                // if none of them
                showAlert(
                    "Unsupported file format",
                    "The selected file could not be recognized. Please upload a valid backup file with a .json or .csv extension.",
                );
                importBtnIndicator.classList.add("hidden!");
            }
        };

        readerFile.readAsText(theFile);
    } else {
        importBtnIndicator.classList.add("hidden!");
        showAlert(
            "Unable to import data",
            "Your session has expired. Please log in again.",
        );
    }
}

// Import action button
importForm.addEventListener("submit", (event) => {
    event.preventDefault();

    if (importBtnIndicator.classList.contains("hidden!")) {
        importBtnIndicator.classList.remove("hidden!");

        hideSupportText(importForm.file_password);
        importData(importForm);
    }
});

// ========== Export option ==========
const radioJson = document.getElementById("option-json");
const radioCsv = document.getElementById("option-csv");
const cryptoSwitch = document.getElementById("crypto-switch");
const csvWarning = document.getElementById("csv-warning");
const securitySection = document.getElementById("security-section");
const passwordBlock = document.getElementById("password-block");
const exportPassword = document.getElementById("export_password");
const exportManifestDesc = document.getElementById("export-manifest-desc");
const exportBtn = document.getElementById("submit_export_btn");
const exportBtnIndicator = exportBtn.querySelector(
    ".button-progress-indicator",
);

const exportDialog = document.getElementById("export-dialog");
const exportForm = document.getElementById("export_form");

// Trigger dialog
async function openExportMenu() {
    await exportDialog.show();
}
async function closeExportMenu() {
    await exportDialog.close();

    exportForm.reset();
    exportForm.export_password.setAttribute("type", "password");
    syncDialogState();
}

// Sync dialog state
function syncDialogState() {
    const isCsvSelected = radioCsv.querySelector("md-radio").checked;
    const isEncryptionEnabled = cryptoSwitch.selected;

    if (isCsvSelected) {
        // Enforce validation rule: CSV files cannot be application-encrypted
        cryptoSwitch.selected = false;
        cryptoSwitch.disabled = true;
        securitySection.classList.add("opacity-40", "pointer-events-none");
        passwordBlock.classList.add("hidden");
        exportPassword.required = false;
        csvWarning.classList.remove("hidden");

        // Update Context Manifest
        exportManifestDesc.innerHTML =
            "Generating <strong>unencrypted .csv spreadsheet</strong>. Contains <span class='underline font-medium'>passwords only</span>. Ready for local browser import pipelines.";
    } else {
        // For json exporting
        cryptoSwitch.disabled = false;
        securitySection.classList.remove("opacity-40", "pointer-events-none");

        if (isEncryptionEnabled) {
            passwordBlock.classList.remove("hidden");
            exportPassword.required = true;
            exportManifestDesc.innerHTML =
                "Generating <strong>secure encrypted .json bundle</strong>. Contains <span class='underline font-medium'>keys and passwords</span> protected via your chosen encryption passphrase.";
        } else {
            passwordBlock.classList.add("hidden");
            exportPassword.value = "";
            exportPassword.required = false;
            exportManifestDesc.innerHTML =
                "Generating <strong>plaintext .json backup</strong>. Contains <span class='underline font-medium'>keys and passwords</span> without secondary protection.";
        }

        csvWarning.classList.add("hidden");
    }
}

// Listener for "Target format" radio button
radioJson.addEventListener("click", () => {
    radioJson.querySelector("md-radio").checked = true;
    syncDialogState();
});

radioCsv.addEventListener("click", () => {
    radioCsv.querySelector("md-radio").checked = true;
    syncDialogState();
});

cryptoSwitch.addEventListener("change", syncDialogState);

// Run initialization hook when components populate
syncDialogState();

// Trigger Export
async function exportData(theForm) {
    const exportAPI = "/api/account/export";

    let formData = new FormData(theForm);
    formData = Object.fromEntries(formData.entries());

    sendRequest(exportAPI, formData, "POST")
        .then((response) => {
            const dataSheet = response.data;

            if (dataSheet.file_type === "csv") {
                // For csv
                const blob = new Blob(["\ufeff", dataSheet.data_sheet], {
                    type: "text/csv;charset=utf-8;",
                });

                tempoaryUrl(blob, "Sunako - Passwords", "csv");
            } else if (dataSheet.file_type === "json") {
                // For json
                const blob = new Blob([dataSheet.json_file], {
                    type: "application/json;charset=utf-8;",
                });

                tempoaryUrl(blob, "Sunako - Keys & Passwords", "json");
            } else {
                // If none of them
                console.error(`Unknown file type! \nerror: ${dataSheet}`);
            }

            showSnackbar(response.message);
            exportBtnIndicator.classList.add("hidden!");
            closeExportMenu();
        })
        .catch((error) => {
            exportBtnIndicator.classList.add("hidden!");
            showAlert("Unable to export data", error.message);
        });
}

// Export action button
exportForm.addEventListener("submit", (event) => {
    event.preventDefault();

    if (exportBtnIndicator.classList.contains("hidden!")) {
        exportBtnIndicator.classList.remove("hidden!");

        exportData(exportForm);
    }
});

// ========== Delete account ==========
async function deleteAccount() {
    const dialogId = "confirm-delete";
    const headline = "Delete account";
    const content =
        "If you delete your account, all keys and passwords you stored will be deleted. Please proceed with caution.";

    const choise = await confirmDialog(dialogId, headline, content);

    if (choise === "delete") {
        // Proceed with account deletion
        try {
            const result = await sendRequest(accountDeletionAPI, {}, "DELETE");
            if (result.code === 200) {
                // Logout the user
                logout();
            }
        } catch (error) {
            showAlert("Unable to delete account", error.message);
        }
    }
}

// ========== Load userdata ==========
async function loadUserData() {
    try {
        const result = await sendRequest(whoami, {}, "GET");

        userdata = {
            name: result.data.name,
            username: result.data.username,
        };

        return true;
    } catch (error) {
        showAlert("Failed to load account data", error.message);
    }
}

// Load user data
loadUserData();

// for enable/disable submit btn
function loadRequired() {
    const targetField = document.querySelectorAll(
        "#edit_account_form md-filled-text-field:not([disabled])",
    );
    const submitBtn = dialogForm.save_changes;

    requireAllFields(targetField, submitBtn);
}
