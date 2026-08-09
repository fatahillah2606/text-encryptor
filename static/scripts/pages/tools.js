// ========== Tabs switcher ==========
const toolsTab = document.getElementById("tools-tab");
const slider = document.querySelector("#slider");

function tabSwitcher(tabIndex) {
    slider.style.transform = `translateX(-${tabIndex * 100}%)`;
}

// Switch tab based url #hash (only run once)
function unActiveTab() {
    toolsTab.tabs.forEach((tab) => {
        tab.active = false;
    });
}

document.body.onload = () => {
    switch (location.hash) {
        case "#encryptor":
            tabSwitcher(0);
            unActiveTab();
            toolsTab.tabs[0].active = true;
            break;

        case "#password_generator":
            tabSwitcher(1);
            unActiveTab();
            toolsTab.tabs[1].active = true;
            break;

        case "#converter":
            tabSwitcher(2);
            unActiveTab();
            toolsTab.tabs[2].active = true;
            break;

        case "#steganography":
            tabSwitcher(3);
            unActiveTab();
            toolsTab.tabs[3].active = true;
            break;

        default:
            break;
    }
};

toolsTab.addEventListener("change", (event) => {
    tabSwitcher(event.target.activeTabIndex);
});

// ========== Text Encryption ==========
let currentState = "encryption";
const encryptorFromLabel = document.getElementById("encryptor-from-label");
const encryptorToLabel = document.getElementById("encryptor-to-label");
const encryptorSwitchBtn = document.getElementById("encryptor-switch-btn");

// Input form
const encryptionForm = document.getElementById("encryption-form");
const encryptorTextInput = encryptionForm.encryptor_input_text;
const encryptorResetInput = encryptionForm.encryptor_reset_input;

// Result form
const encryptResult = document.getElementById("encryptor-result");
const encryptorCopyBtn = document.getElementById("encryptor-copy-btn");
let encryptor_api = "/api/encryptor/encrypt_text";

// Encryptor tab switcher
const encryptorTab = document.getElementById("encryptor-tab-switcher");
const encryptorSlider = document.querySelector("#encryptor-slider");

function encryptorTabSwitcher(tabIndex) {
    encryptorSlider.style.transform = `translateX(-${tabIndex * 100}%)`;
}

encryptorTab.addEventListener("change", (event) => {
    encryptorTabSwitcher(event.target.activeTabIndex);
});

// Switch encryption state
function switchEncryptionState() {
    // Disable the switch button
    encryptorSwitchBtn.disabled = true;

    // Move the value from result to input text
    encryptorTextInput.value = encryptResult.value;

    // Change the state
    if (currentState === "encryption") {
        currentState = "decryption";
        encryptor_api = "/api/encryptor/decrypt_text";

        encryptorFromLabel.textContent = "Encrypted text";
        encryptorToLabel.textContent = "Plain text";
        encryptResult.placeholder = "Decrypted";
    } else {
        currentState = "encryption";
        encryptor_api = "/api/encryptor/encrypt_text";

        encryptorFromLabel.textContent = "Plain text";
        encryptorToLabel.textContent = "Encrypted text";
        encryptResult.placeholder = "Encrypted";
    }

    // Readjust the encryptorTextInput
    adjustFontSize(encryptorTextInput);
    autoResizeTextarea(encryptorTextInput);

    // reprocess the encryption
    proceedEncryption();

    // Wait for a while to re-enable the switch button
    setTimeout(() => {
        encryptorSwitchBtn.disabled = false;
    }, 500);
}

encryptorSwitchBtn.addEventListener("click", switchEncryptionState);

// Encrypt function
async function proceedEncryption() {
    if (encryptorTextInput.value.trim()) {
        encryptorResetInput.classList.remove("hidden!");
        encryptorCopyBtn.classList.remove("hidden!");
    } else {
        encryptResult.value = "";
        encryptorResetInput.classList.add("hidden!");
        encryptorCopyBtn.classList.add("hidden!");
        return;
    }

    let encryptionKey = sessionStorage.getItem("encryption_key");
    encryptionKey = JSON.parse(encryptionKey);

    if (encryptionKey) {
        let formData = new FormData(encryptionForm);
        formData.append("key", encryptionKey.key);
        formData = Object.fromEntries(formData.entries());

        // send request
        try {
            const result = await sendRequest(encryptor_api, formData, "POST");
            if (result.code === 200) {
                encryptResult.value = result.data.result_text;
                adjustFontSize(encryptResult);
                autoResizeTextarea(encryptResult);
            }
        } catch (error) {
            encryptResult.value = error.message;
            adjustFontSize(encryptResult);
            autoResizeTextarea(encryptResult);
        }
    } else {
        // Trigger encryption key modal
        checkEncryptionKey();
    }
}

// Reset input state
function encryptorResetInputState() {
    resetTextarea(encryptorTextInput);
    resetTextarea(encryptResult);

    encryptorResetInput.classList.add("hidden!");
    proceedEncryption();
}

if (encryptorTextInput) {
    const debouncedState = debounce(proceedEncryption, 300);
    encryptorTextInput.addEventListener("input", (e) => {
        debouncedState();

        adjustFontSize(e.target);
        autoResizeTextarea(e.target);
    });

    // Run once on load in case there is pre-filled text
    adjustFontSize(encryptorTextInput);
    autoResizeTextarea(encryptorTextInput);

    adjustFontSize(encryptResult);
    autoResizeTextarea(encryptResult);

    if (encryptorTextInput.value.trim()) {
        encryptorResetInput.classList.remove("hidden!");
        encryptorCopyBtn.classList.remove("hidden!");
    }
}

// The X button
encryptorResetInput.addEventListener("click", encryptorResetInputState);

// ========== Share option ==========
const shareModal = document.getElementById("share-modal");
const shareForm = document.getElementById("share_form");
const outputLink = document.getElementById("generated_link");
const regenerateBtn = document.getElementById("regenerate_btn");
const linkSpan = document.getElementById("link-span");

const generateLinkAPI = "/api/encryptor/generate_link";

// Generate link
async function generate_link(textToShare, targetElm, noticeBanner) {
    data = { text_to_share: textToShare };
    try {
        // Get generated link
        const result = await sendRequest(generateLinkAPI, data, "POST");

        if (targetElm.value !== undefined) {
            targetElm.value = result.data.link;
        } else {
            targetElm.textContent = result.data.link;
        }

        // Link span
        const currentTime = new Date();
        currentTime.setMinutes(currentTime.getMinutes() + 5);

        let hour = currentTime.getHours();
        let minute = currentTime.getMinutes();

        hour = hour < 10 ? "0" + hour : hour;
        minute = minute < 10 ? "0" + minute : minute;

        let bannerText = `The link is valid until ${hour}:${minute}`;

        noticeBanner.classList.remove("hidden");
        noticeBanner.querySelector("span:nth-child(2)").textContent =
            bannerText;

        showSnackbar(result.message);
    } catch (error) {
        showAlert("Unable to generate link", error.message);
    }
}

// Open share modal
async function openShareModal() {
    // Reset everything first
    shareForm.reset();
    linkSpan.classList.add("hidden");
    hideSupportText(shareForm.text_to_share);

    shareForm.text_to_share.value = encryptionForm.encryptor_input_text.value;
    await shareModal.show();
}

// Close share modal
async function closeShareModal() {
    await shareModal.close();
}

// Generate link button
regenerateBtn.addEventListener("click", () => {
    hideSupportText(shareForm.text_to_share);

    if (shareForm.text_to_share.value.trim() !== "") {
        generate_link(shareForm.text_to_share.value, outputLink, linkSpan);
    } else {
        showSupportText(
            shareForm.text_to_share,
            "Enter the text you want to share.",
        );
    }
});

// ========== File Encryptor ==========
let currentDownloadUrl = null;

function encryptorSendFile(
    uploadAPI,
    fileInput,
    keyInput,
    progressIndicator,
    downloadButton,
) {
    // Remove supporting text on keyInput
    hideSupportText(keyInput);

    // Check file and key input
    if (!fileInput.files[0] || !keyInput.value) return;

    const circularProgress = progressIndicator.querySelector(
        "md-circular-progress",
    );

    // Clean up previous blob URL if the user is processing a new file and hide download button during process
    if (currentDownloadUrl) {
        window.URL.revokeObjectURL(currentDownloadUrl);
        currentDownloadUrl = null;

        encryptorDownloadButton.classList.add("hidden");
        decryptorDownloadButton.classList.add("hidden");
    }

    const formData = new FormData();
    formData.append("file", fileInput.files[0]);
    formData.append("key", keyInput.value);

    const xhr = new XMLHttpRequest();
    xhr.open("POST", uploadAPI, true);

    // handle binary file download
    xhr.responseType = "blob";

    // Track upload progress
    xhr.upload.onprogress = function (e) {
        if (e.lengthComputable) {
            const percentComplete = (e.loaded / e.total) * 100;
            circularProgress.removeAttribute("indeterminate");
            circularProgress.setAttribute("value", percentComplete / 100);
        }
    };

    // Switch the progress indicator to indeterminate mode
    xhr.upload.onload = function () {
        circularProgress.removeAttribute("value");
        circularProgress.setAttribute("indeterminate", "");
    };

    xhr.onload = function () {
        if (xhr.status === 200) {
            // Extract filename sent from backend Content-Disposition header
            let downloadName = fileInput.files[0].name; // Fallback
            const disposition = xhr.getResponseHeader("Content-Disposition");

            if (disposition) {
                // Try RFC 5987 encoding (filename*=UTF-8''...)
                const utf8Matches = /filename\*=UTF-8''([^;\n]*)/i.exec(
                    disposition,
                );
                if (utf8Matches && utf8Matches[1]) {
                    downloadName = decodeURIComponent(utf8Matches[1]);
                } else {
                    // Fall back to standard filename="..."
                    const standardMatches = /filename="?([^";\n]*)"?/i.exec(
                        disposition,
                    );
                    if (standardMatches && standardMatches[1]) {
                        downloadName = standardMatches[1];
                    }
                }
            }

            // Create a temporary link to trigger file download
            const blob = xhr.response;
            currentDownloadUrl = window.URL.createObjectURL(blob);

            // Attach to the Download button
            downloadButton.classList.remove("hidden");
            downloadButton.onclick = function () {
                const a = document.createElement("a");
                a.href = currentDownloadUrl;
                a.download = downloadName;
                document.body.appendChild(a);
                a.click();
                a.remove();
            };

            // Success feedback
            showSnackbar("The process was successfully completed.");
            resetUploadButton();
        } else {
            const reader = new FileReader();

            reader.onload = function () {
                try {
                    const responseJson = JSON.parse(reader.result);
                    const errorMessage =
                        responseJson.message ||
                        "An unknown error occurred. Please try again";

                    showSupportText(keyInput, errorMessage);
                } catch (e) {
                    showAlert(
                        "Unable to process file",
                        "Process failed. Please try again.",
                    );
                }
                resetUploadButton();
            };

            // Read binary blob response
            reader.readAsText(xhr.response);
        }
    };

    xhr.onerror = function () {
        showAlert(
            "Unable to upload file",
            "Network error occurred. Please try again.",
        );
        resetUploadButton();
    };

    xhr.send(formData);

    function resetUploadButton() {
        progressIndicator.classList.add("hidden!");
        circularProgress.value = 0;
    }
}

// Show file card, hide drop zone
function encryptorShowFileState(
    file,
    fileName,
    dropZone,
    fileInfoContainer,
    nextStep,
) {
    if (!file) return;

    // Display the file name
    fileName.textContent = `${file.name} (${formatFileSize(file.size)})`;
    dropZone.style.display = "none";
    fileInfoContainer.style.display = "flex";

    // Display the next step
    nextStep.classList.remove("hidden");
}

// Reset back to upload drop zone state
function encryptorResetFileState(
    fileInput,
    keyInput,
    fileInfoContainer,
    dropZone,
    nextStep,
    downloadButton,
) {
    fileInput.value = ""; // Clear file buffer
    fileInfoContainer.style.display = "none";
    dropZone.style.display = "flex";
    nextStep.classList.add("hidden");
    downloadButton.classList.add("hidden");

    hideSupportText(keyInput);
    keyInput.value = "";

    if (currentDownloadUrl) {
        window.URL.revokeObjectURL(currentDownloadUrl);
        currentDownloadUrl = null;
    }
}

// ========== For encryption ==========
const encryptorFileForm = document.getElementById("file_encrypt_form");
const encryptorBrowseBtn = document.getElementById("encryptor-browse-btn");
const encryptorFileInput = document.getElementById("encryptor_file_input");
const encryptorDropZone = document.getElementById("encryptor-drop-zone");
const encryptorFileInfo = document.getElementById("encryptor-file-info");
const encryptorFileNameSpan = document.getElementById("encryptor-file-name");
const encryptorClearFileBtn = document.getElementById(
    "encryptor-clear-file-btn",
);
const encryptorNextStep = document.getElementById("encryptor-next-step");
const encryptorButton = document.getElementById("encrypt_submit_btn");
const encryptorProgressIndicator = encryptorButton.querySelector(
    ".button-progress-indicator",
);
const encryptorDownloadButton = document.getElementById("download-encrypted");

const fileEncryptAPI = "/api/encryptor/encrypt_file";

// Native trigger
encryptorBrowseBtn.addEventListener("click", () => encryptorFileInput.click());

encryptorFileInput.addEventListener("change", (e) => {
    if (e.target.files.length > 0) {
        encryptorShowFileState(
            e.target.files[0],
            encryptorFileNameSpan,
            encryptorDropZone,
            encryptorFileInfo,
            encryptorNextStep,
        );
    }
});

// Clear selection click event
encryptorClearFileBtn.addEventListener("click", () => {
    encryptorResetFileState(
        encryptorFileInput,
        encryptorFileForm.encrypt_key,
        encryptorFileInfo,
        encryptorDropZone,
        encryptorNextStep,
        encryptorDownloadButton,
    );
});

// Drag-and-drop handles
encryptorDropZone.addEventListener("dragover", (e) => {
    e.preventDefault();
    encryptorDropZone.classList.add("drag-over");
});

encryptorDropZone.addEventListener("dragleave", () => {
    encryptorDropZone.classList.remove("drag-over");
});

encryptorDropZone.addEventListener("drop", (e) => {
    e.preventDefault();
    encryptorDropZone.classList.remove("drag-over");

    if (e.dataTransfer.files.length > 0) {
        const droppedFile = e.dataTransfer.files[0];
        const extension = droppedFile.name.split(".").pop().toLowerCase();

        encryptorFileInput.files = e.dataTransfer.files;
        encryptorShowFileState(
            droppedFile,
            encryptorFileNameSpan,
            encryptorDropZone,
            encryptorFileInfo,
            encryptorNextStep,
        );
    }
});

// File Encryption process
encryptorFileForm.addEventListener("submit", (event) => {
    event.preventDefault();

    if (encryptorProgressIndicator.classList.contains("hidden!")) {
        encryptorProgressIndicator.classList.remove("hidden!");

        encryptorSendFile(
            fileEncryptAPI,
            encryptorFileInput,
            encryptorFileForm.encrypt_key,
            encryptorProgressIndicator,
            encryptorDownloadButton,
        );
    }
});

// ========== For decryption ==========
const decryptorFileForm = document.getElementById("file_decrypt_form");
const decryptorBrowseBtn = document.getElementById("decryptor-browse-btn");
const decryptorFileInput = document.getElementById("decryptor_file_input");
const decryptorDropZone = document.getElementById("decryptor-drop-zone");
const decryptorFileInfo = document.getElementById("decryptor-file-info");
const decryptorFileNameSpan = document.getElementById("decryptor-file-name");
const decryptorClearFileBtn = document.getElementById(
    "decryptor-clear-file-btn",
);
const decryptorNextStep = document.getElementById("decryptor-next-step");
const decryptorButton = document.getElementById("decrypt_submit_btn");
const decryptorProgressIndicator = decryptorButton.querySelector(
    ".button-progress-indicator",
);
const decryptorDownloadButton = document.getElementById("download-decrypted");

const fileDecryptAPI = "/api/encryptor/decrypt_file";

// Native trigger
decryptorBrowseBtn.addEventListener("click", () => decryptorFileInput.click());

decryptorFileInput.addEventListener("change", (e) => {
    if (e.target.files.length > 0) {
        encryptorShowFileState(
            e.target.files[0],
            decryptorFileNameSpan,
            decryptorDropZone,
            decryptorFileInfo,
            decryptorNextStep,
        );
    }
});

// Clear selection click event
decryptorClearFileBtn.addEventListener("click", () => {
    encryptorResetFileState(
        decryptorFileInput,
        decryptorFileForm.decrypt_key,
        decryptorFileInfo,
        decryptorDropZone,
        decryptorNextStep,
        decryptorDownloadButton,
    );
});

// Drag-and-drop handles
decryptorDropZone.addEventListener("dragover", (e) => {
    e.preventDefault();
    decryptorDropZone.classList.add("drag-over");
});

decryptorDropZone.addEventListener("dragleave", () => {
    decryptorDropZone.classList.remove("drag-over");
});

decryptorDropZone.addEventListener("drop", (e) => {
    e.preventDefault();
    decryptorDropZone.classList.remove("drag-over");

    if (e.dataTransfer.files.length > 0) {
        const droppedFile = e.dataTransfer.files[0];
        const extension = droppedFile.name.split(".").pop().toLowerCase();

        if (extension === "sunako") {
            decryptorFileInput.files = e.dataTransfer.files;
            encryptorShowFileState(
                droppedFile,
                decryptorFileNameSpan,
                decryptorDropZone,
                decryptorFileInfo,
                decryptorNextStep,
            );
        } else {
            showAlert(
                "Unsupported file format",
                "The selected file could not be recognized. Please upload a valid encrypted file with a .sunako extension.",
            );
        }
    }
});

// File Decryption process
decryptorFileForm.addEventListener("submit", (event) => {
    event.preventDefault();

    if (decryptorProgressIndicator.classList.contains("hidden!")) {
        decryptorProgressIndicator.classList.remove("hidden!");

        encryptorSendFile(
            fileDecryptAPI,
            decryptorFileInput,
            decryptorFileForm.decrypt_key,
            decryptorProgressIndicator,
            decryptorDownloadButton,
        );
    }
});

// ========== Password Generator ==========
const passwordGeneratorForm = document.getElementById(
    "password_generator_form",
);

const generatedPassword = document.getElementById("generated_password");
const encryptedGeneratedPassword = document.getElementById(
    "encrypted_generated_password",
);

const password_generator_api = "/api/encryptor/password_generator";

async function generatePassword() {
    let encryptionKey = sessionStorage.getItem("encryption_key");
    encryptionKey = JSON.parse(encryptionKey);

    if (encryptionKey) {
        let formData = new FormData(passwordGeneratorForm);
        formData.append("key", encryptionKey.key);

        if (passwordGeneratorForm.encrypt_password.checked) {
            formData.set("encrypt_password", 1);
        } else {
            formData.append("encrypt_password", 0);
        }

        formData = Object.fromEntries(formData.entries());

        // send request
        try {
            const result = await sendRequest(
                password_generator_api,
                formData,
                "POST",
            );

            generatedPassword.textContent = result.data.password;
            encryptedGeneratedPassword.textContent =
                result.data.encrypted_password;

            showSnackbar(result.message);
        } catch (error) {
            showAlert("Unable to generate password", error.message);
        }
    } else {
        // Trigger encryption key modal
        checkEncryptionKey();
    }
}

passwordGeneratorForm.addEventListener("submit", (event) => {
    event.preventDefault();
    generatePassword();
});

// ========== Text Converter ==========
let reverseConvert = false;

const converterLabelParent = document.getElementById("converter-labels");
const converterLabels = document.querySelectorAll("#converter-labels > div");
const converterSwitchBtn = document.getElementById("converter-switch-btn");

// Input form
const converterForm = document.getElementById("converter-form");
const converterTextInput = converterForm.converter_input_text;
const converterResetInput = converterForm.converter_reset_input;

// Result form
const converterResult = document.getElementById("converter-result");
const converterCopyBtn = document.getElementById("converter-copy-btn");
let converter_api = "/api/converter";

// Reverse convertion
function reverseConvertion() {
    converterSwitchBtn.disabled = true;
    converterTextInput.value = converterResult.value;

    if (reverseConvert) {
        converterLabelParent.style.direction = "ltr";

        converterLabels.forEach((label) => {
            label.classList.remove("sm:justify-end");
            label.classList.add("sm:justify-start");
        });

        converterResult.placeholder = "Encoded";
        reverseConvert = false;
    } else {
        converterLabelParent.style.direction = "rtl";

        converterLabels.forEach((label) => {
            label.classList.add("sm:justify-end");
            label.classList.remove("sm:justify-start");
        });

        converterResult.placeholder = "Decoded";
        reverseConvert = true;
    }

    proceedConverter();

    setTimeout(() => {
        converterSwitchBtn.disabled = false;
    }, 500);
}

converterSwitchBtn.addEventListener("click", reverseConvertion);

// Convert function
async function proceedConverter() {
    if (converterTextInput.value.trim()) {
        converterResetInput.classList.remove("hidden!");
        converterCopyBtn.classList.remove("hidden!");
    } else {
        converterResult.value = "";
        converterResetInput.classList.add("hidden!");
        converterCopyBtn.classList.add("hidden!");
        return;
    }

    let formData = new FormData(converterForm);
    formData.append("reverse_convert", reverseConvert);
    formData = Object.fromEntries(formData.entries());

    // Send request
    try {
        const result = await sendRequest(converter_api, formData, "POST");
        if (result.code === 200) {
            converterResult.value = result.data.result_text;
            adjustFontSize(converterResult);
            autoResizeTextarea(converterResult);
        }
    } catch (error) {
        converterResult.value = error.message;
        adjustFontSize(converterResult);
        autoResizeTextarea(converterResult);
    }
}

// Reset input state
function converterResetInputState() {
    converterTextInput.value = "";

    resetTextarea(converterTextInput);
    resetTextarea(converterResult);

    converterResetInput.classList.add("hidden!");
    proceedConverter();
}

if (converterTextInput) {
    const debouncedState = debounce(proceedConverter, 300);
    converterTextInput.addEventListener("input", (e) => {
        debouncedState();

        adjustFontSize(e.target);
        autoResizeTextarea(e.target);
    });

    // Run once on load in case there is pre-filled text
    adjustFontSize(converterTextInput);
    autoResizeTextarea(converterTextInput);

    adjustFontSize(converterResult);
    autoResizeTextarea(converterResult);

    if (converterTextInput.value.trim()) {
        converterResetInput.classList.remove("hidden!");
        converterCopyBtn.classList.remove("hidden!");
    }
}

// The X button on textfield
converterResetInput.addEventListener("click", converterResetInputState);

// Start convertion on option change
converterForm.convert_to_option.addEventListener("change", () => {
    const debouncedState = debounce(proceedConverter, 300);
    debouncedState();
});

// ========== Steganography ==========

// Show file info card, hide file selector button
function steganographyShowFileState(
    file,
    selectBtnContainer,
    fileName,
    fileInfoContainer,
) {
    if (!file) return;

    // Display file info
    fileName.textContent = `${file.name} (${formatFileSize(file.size)})`;
    selectBtnContainer.classList.add("hidden");
    fileInfoContainer.classList.remove("hidden!");
}

// Reset back file selector button, hide file info card
function steganographyResetFileState(
    fileInput,
    selectBtnContainer,
    fileInfoContainer,
) {
    fileInput.value = "";
    selectBtnContainer.classList.remove("hidden");
    fileInfoContainer.classList.add("hidden!");
}

// ========== For hiding the secret ==========
const hideSecretForm = document.getElementById("hide-secret-form");
const typeSelector = hideSecretForm.type_selector;
const secretMessageContainer = document.getElementById(
    "secret-message-container",
);

let secretType = "text";

// Type selection listener
typeSelector.addEventListener("change", () => {
    secretMessageContainer.classList.add("hidden");
    secretFileContainer.classList.add("hidden");

    // Reset secret message state
    hideSecretForm.secret_message.value = "";

    // Reset secret file state
    steganographyResetFileState(
        secretFileInput,
        secretFileChooser,
        secretFileInfo,
    );

    if (typeSelector.value === "plain-text") {
        hideSecretForm.secret_message.required = true;
        secretMessageContainer.classList.remove("hidden");
    } else {
        hideSecretForm.secret_message.required = false;
        secretFileContainer.classList.remove("hidden");
    }
});

// For secret file
const secretFileContainer = document.getElementById("secret-file-container");
const secretFileChooser = document.getElementById("secret-file-chooser");
const secretFileInput = hideSecretForm.secret_file_input;
const secretFileInputBtn = document.getElementById("secret-file-select-btn");

const secretFileInfo = document.getElementById("secret-file-info");
const secretFileName = document.getElementById("secret-file-name");
const secretFileClearBtn = document.getElementById("secret-file-clear-btn");

secretFileInputBtn.addEventListener("click", () => secretFileInput.click());

secretFileInput.addEventListener("change", (e) => {
    if (e.target.files.length > 0) {
        steganographyShowFileState(
            e.target.files[0],
            secretFileChooser,
            secretFileName,
            secretFileInfo,
        );
    }
});

secretFileClearBtn.addEventListener("click", () => {
    steganographyResetFileState(
        secretFileInput,
        secretFileChooser,
        secretFileInfo,
    );
});

// For media carrier
const mediaCarrierChooser = document.getElementById("media-carrier-chooser");
const mediaCarrierInput = hideSecretForm.media_carrier_input;
const mediaCarrierInputBtn = document.getElementById(
    "media-carrier-select-btn",
);

const mediaCarrierInfo = document.getElementById("media-carrier-info");
const mediaCarrierName = document.getElementById("media-carrier-name");
const mediaCarrierClearBtn = document.getElementById("media-carrier-clear-btn");

mediaCarrierInputBtn.addEventListener("click", () => mediaCarrierInput.click());

mediaCarrierInput.addEventListener("change", (e) => {
    if (e.target.files.length > 0) {
        steganographyShowFileState(
            e.target.files[0],
            mediaCarrierChooser,
            mediaCarrierName,
            mediaCarrierInfo,
        );
    }
});

mediaCarrierClearBtn.addEventListener("click", () => {
    steganographyResetFileState(
        mediaCarrierInput,
        mediaCarrierChooser,
        mediaCarrierInfo,
    );
});

// Security settings
// Enable encryption
const enableEncryptionCheckbox = hideSecretForm.enable_encryption;
const encryptSecretPassField = document.getElementById(
    "encrypt-secret-pass-field",
);

function enableEncryption() {
    // Setting the timeout for fixing stupid bug checkbox checked issue
    setTimeout(() => {
        if (hideSecretForm.enable_encryption.checked) {
            encryptSecretPassField.classList.remove("hidden");
            hideSecretForm.secret_password.required = true;
        } else {
            encryptSecretPassField.classList.add("hidden");
            hideSecretForm.secret_password.required = false;
        }
    }, 50);
}

enableEncryptionCheckbox.addEventListener("click", enableEncryption);
