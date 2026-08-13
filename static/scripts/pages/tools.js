// ========== Global functions ==========

// Auto-resize textarea height
function autoResizeTextarea(textarea) {
    textarea.style.height = "auto";
    if (textarea.scrollHeight <= 320) {
        textarea.style.height = `${textarea.scrollHeight}px`;
    } else {
        textarea.style.height = "320px";
    }
}

// Dynamic font scaling based on character length
function adjustFontSize(textarea) {
    const length = textarea.value.length;

    if (length > 300) {
        textarea.classList.remove("sm:text-xl");
    } else {
        textarea.classList.add("sm:text-xl");
    }
}

function resetTextarea(textarea) {
    textarea.value = "";
    textarea.style.height = "auto";
    textarea.classList.add("sm:text-xl");
}

// Renders and appends file info items for an input file element
function renderFileInputList(
    container,
    fileInput,
    inputBtn,
    onFileRemoved,
    nextStep = null,
    clearBlobUrl = null,
) {
    if (!container || !fileInput || !fileInput.files.length) return;

    // Ensure container is visible and clear previous result cards
    container.classList.remove("hidden!");
    container.innerHTML = "";

    Array.from(fileInput.files).forEach((file) => {
        const fileInfoCard = document.createElement("div");
        fileInfoCard.className = "file-info";

        const fileDetails = document.createElement("div");
        fileDetails.className = "file-details";

        // Dynamic Icon
        const icon = document.createElement("md-icon");
        icon.textContent = getMaterialFileIcon(file.name);

        // File Name & Size Label
        const fileTextContainer = document.createElement("div");
        fileTextContainer.className = "flex flex-col min-w-0 flex-1";

        const fileNameSpan = document.createElement("span");
        fileNameSpan.className =
            "md-typescale-body-medium text-md-on-surface m-0 truncate";
        fileNameSpan.textContent = file.name;

        const fileSizeSpan = document.createElement("span");
        fileSizeSpan.className =
            "md-typescale-label-small text-md-on-surface-variant m-0";
        fileSizeSpan.textContent = formatFileSize(file.size);

        fileTextContainer.appendChild(fileNameSpan);
        fileTextContainer.appendChild(fileSizeSpan);

        // Clear / Remove Button
        const clearBtn = document.createElement("md-icon-button");
        clearBtn.type = "button";
        clearBtn.setAttribute("aria-label", "Clear selected file");
        clearBtn.className = "shrink-0!";

        const closeIcon = document.createElement("md-icon");
        closeIcon.textContent = "close";
        clearBtn.appendChild(closeIcon);

        // Delete specific file from input list using exact file reference match
        clearBtn.addEventListener("click", () => {
            const dt = new DataTransfer();

            // Compare file objects directly to avoid index mismatch on fast clicking
            Array.from(fileInput.files).forEach((f) => {
                const isTargetFile =
                    f === file ||
                    (f.name === file.name &&
                        f.size === file.size &&
                        f.lastModified === file.lastModified);

                if (!isTargetFile) {
                    dt.items.add(f);
                }
            });

            fileInput.files = dt.files;
            fileInfoCard.remove();

            if (fileInput.files.length === 0) {
                container.classList.add("hidden!");
                inputBtn.classList.remove("hidden");

                // If it has next step section
                if (nextStep) {
                    nextStep.classList.add("hidden");
                }

                // For clearing download URL
                if (clearBlobUrl) {
                    clearResultFileInfo(clearBlobUrl);
                }
            }

            if (onFileRemoved) onFileRemoved(fileInput.files);
        });

        fileDetails.appendChild(icon);
        fileDetails.appendChild(fileTextContainer);
        fileDetails.appendChild(clearBtn);
        fileInfoCard.appendChild(fileDetails);

        container.appendChild(fileInfoCard);

        inputBtn.classList.add("hidden");

        // If it has next step section
        if (nextStep) {
            nextStep.classList.remove("hidden");
        }
    });
}

// Renders a result file card from a Blob object and appends it to a container
function renderResultFileInfo(container, blobFile, fileName) {
    if (!container || !blobFile) return;

    // Ensure container is visible and clear previous result cards
    container.classList.remove("hidden!");
    container.innerHTML = "";

    // Create object URL for download
    const blobUrl = window.URL.createObjectURL(blobFile);

    const fileInfoCard = document.createElement("div");
    fileInfoCard.className = "file-info";

    const fileDetails = document.createElement("div");
    fileDetails.className = "file-details flex items-center gap-2";

    // Dynamic Icon
    const icon = document.createElement("md-icon");
    icon.textContent = getMaterialFileIcon(fileName);

    // Text Wrapper
    const fileTextContainer = document.createElement("div");
    fileTextContainer.className = "flex flex-col min-w-0 flex-1";

    const fileNameSpan = document.createElement("span");
    fileNameSpan.className =
        "md-typescale-body-medium text-md-on-surface m-0 truncate";
    fileNameSpan.textContent = fileName;

    const fileSizeSpan = document.createElement("span");
    fileSizeSpan.className =
        "md-typescale-label-small text-md-on-surface-variant m-0";
    fileSizeSpan.textContent = formatFileSize(blobFile.size);

    fileTextContainer.appendChild(fileNameSpan);
    fileTextContainer.appendChild(fileSizeSpan);

    // Download Button
    const downloadBtn = document.createElement("md-icon-button");
    downloadBtn.type = "button";
    downloadBtn.setAttribute("aria-label", "Download result file");
    downloadBtn.className = "shrink-0!";

    const downloadIcon = document.createElement("md-icon");
    downloadIcon.textContent = "download";
    downloadBtn.appendChild(downloadIcon);

    // Trigger file download on click
    downloadBtn.addEventListener("click", () => {
        const downloadLink = document.createElement("a");
        downloadLink.href = blobUrl;
        downloadLink.download = fileName;
        document.body.appendChild(downloadLink);
        downloadLink.click();
        downloadLink.remove();
    });

    // Store blobUrl on element dataset for cleanup later
    fileInfoCard.dataset.blobUrl = blobUrl;

    // Assemble DOM hierarchy
    fileDetails.appendChild(icon);
    fileDetails.appendChild(fileTextContainer);
    fileDetails.appendChild(downloadBtn);
    fileInfoCard.appendChild(fileDetails);

    container.appendChild(fileInfoCard);
}

// Clears result file cards from a container and revokes memory Object URLs
function clearResultFileInfo(container) {
    if (!container) return;

    // Revoke Object URLs to prevent memory leaks
    const cards = container.querySelectorAll(".file-info");
    cards.forEach((card) => {
        if (card.dataset.blobUrl) {
            window.URL.revokeObjectURL(card.dataset.blobUrl);
        }
    });

    container.innerHTML = "";
    container.classList.add("hidden!");
}

// Renders a result plain text from a JSON response and appends it to a container
function renderResultText(container, secretMessage) {
    if (!container || !secretMessage) return;

    // Ensure container is visible and clear previous result cards
    container.classList.remove("hidden!");
    container.innerHTML = "";

    // Create md-outlined-text-field for displaying the secret message
    const mdTextField = document.createElement("md-outlined-text-field");
    mdTextField.type = "textarea";
    mdTextField.id = "revealed-message";
    mdTextField.className = "w-full resize-y mb-2.5";
    mdTextField.placeholder = "Revealed secret message will shown here...";
    mdTextField.setAttribute("rows", "3");
    mdTextField.value = secretMessage;

    // Create copy button
    const mdCopyBtn = document.createElement("md-filled-tonal-button");
    mdCopyBtn.type = "button";
    mdCopyBtn.textContent = "Copy";

    mdCopyBtn.addEventListener("click", (e) => {
        copyText("revealed-message", e.target);
    });

    // Assemble
    container.appendChild(mdTextField);
    container.appendChild(mdCopyBtn);
}

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
function encryptorSendFile(
    uploadAPI,
    fileInput,
    keyInput,
    progressIndicator,
    resultFile,
) {
    // Remove supporting text on keyInput
    hideSupportText(keyInput);

    // Check file and key input
    if (!fileInput.files || !keyInput.value) return;

    const circularProgress = progressIndicator.querySelector(
        "md-circular-progress",
    );

    // Clean up previous blob URL if the user is processing a new file and hide download button during process
    clearResultFileInfo(resultFile);

    const formData = new FormData();
    formData.append("key", keyInput.value);

    // Proceed multiple file
    Array.from(fileInput.files).forEach((file) => {
        formData.append("files", file);
    });

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
            renderResultFileInfo(resultFile, blob, downloadName);

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

// ========== For encryption ==========
const encryptorFileForm = document.getElementById("file_encrypt_form");
const encryptorBrowseBtn = document.getElementById("encryptor-browse-btn");
const encryptorFileInput = document.getElementById("encryptor_file_input");
const encryptorDropZone = document.getElementById("encryptor-drop-zone");
const encryptorFileInfo = document.getElementById("encryptor-file-info");

const encryptorNextStep = document.getElementById("encryptor-next-step");
const encryptorButton = document.getElementById("encrypt_submit_btn");
const encryptorProgressIndicator = encryptorButton.querySelector(
    ".button-progress-indicator",
);
const encryptResultContainer = document.getElementById(
    "encrypt-result-container",
);

const fileEncryptAPI = "/api/encryptor/encrypt_file";
let accumulatedEncryptFiles = new DataTransfer();

// Native trigger
encryptorBrowseBtn.addEventListener("click", () => encryptorFileInput.click());
encryptorFileInput.addEventListener("change", (e) => {
    // Merge new selections into accumulated list
    Array.from(decoderFileInput.files).forEach((file) => {
        accumulatedEncryptFiles.items.add(file);
    });

    // Update the input element's files
    decoderFileInput.files = accumulatedEncryptFiles.files;

    // Render accumulated list
    renderFileInputList(
        encryptorFileInfo,
        encryptorFileInput,
        encryptorDropZone,
        (updatedFiles) => {
            // Sync DataTransfer when items are deleted via close button
            accumulatedEncryptFiles = new DataTransfer();
            Array.from(updatedFiles).forEach((f) =>
                accumulatedEncryptFiles.items.add(f),
            );
        },
        encryptorNextStep,
        encryptResultContainer,
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

        // Merge new selections into accumulated list
        Array.from(decoderFileInput.files).forEach((file) => {
            accumulatedEncryptFiles.items.add(file);
        });

        // Update the input element's files
        decoderFileInput.files = accumulatedEncryptFiles.files;

        // Render accumulated list
        renderFileInputList(
            encryptorFileInfo,
            encryptorFileInput,
            encryptorDropZone,
            (updatedFiles) => {
                // Sync DataTransfer when items are deleted via close button
                accumulatedEncryptFiles = new DataTransfer();
                Array.from(updatedFiles).forEach((f) =>
                    accumulatedEncryptFiles.items.add(f),
                );
            },
            encryptorNextStep,
            encryptResultContainer,
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
            encryptResultContainer,
        );
    }
});

// ========== For decryption ==========
const decryptorFileForm = document.getElementById("file_decrypt_form");
const decryptorBrowseBtn = document.getElementById("decryptor-browse-btn");
const decryptorFileInput = document.getElementById("decryptor_file_input");
const decryptorDropZone = document.getElementById("decryptor-drop-zone");
const decryptorFileInfo = document.getElementById("decryptor-file-info");

const decryptorNextStep = document.getElementById("decryptor-next-step");
const decryptorButton = document.getElementById("decrypt_submit_btn");
const decryptorProgressIndicator = decryptorButton.querySelector(
    ".button-progress-indicator",
);
const decryptorResultContainer = document.getElementById(
    "decrypt-result-container",
);

const fileDecryptAPI = "/api/encryptor/decrypt_file";
let accumulatedDecryptFiles = new DataTransfer();

// Native trigger
decryptorBrowseBtn.addEventListener("click", () => decryptorFileInput.click());
decryptorFileInput.addEventListener("change", () => {
    // Merge new selections into accumulated list
    Array.from(decoderFileInput.files).forEach((file) => {
        accumulatedDecryptFiles.items.add(file);
    });

    // Update the input element's files
    decoderFileInput.files = accumulatedDecryptFiles.files;

    // Render accumulated list
    renderFileInputList(
        decryptorFileInfo,
        decryptorFileInput,
        decryptorDropZone,
        (updatedFiles) => {
            // Sync DataTransfer when items are deleted via close button
            accumulatedDecryptFiles = new DataTransfer();
            Array.from(updatedFiles).forEach((f) =>
                accumulatedDecryptFiles.items.add(f),
            );
        },
        decryptorNextStep,
        decryptorResultContainer,
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

            // Merge new selections into accumulated list
            Array.from(decoderFileInput.files).forEach((file) => {
                accumulatedDecryptFiles.items.add(file);
            });

            // Update the input element's files
            decoderFileInput.files = accumulatedDecryptFiles.files;

            // Render accumulated list
            renderFileInputList(
                decryptorFileInfo,
                decryptorFileInput,
                decryptorDropZone,
                (updatedFiles) => {
                    // Sync DataTransfer when items are deleted via close button
                    accumulatedDecryptFiles = new DataTransfer();
                    Array.from(updatedFiles).forEach((f) =>
                        accumulatedDecryptFiles.items.add(f),
                    );
                },
                decryptorNextStep,
                decryptorResultContainer,
            );
        } else {
            showAlert(
                "Unsupported file format",
                "One of the selected files could not be recognized. Please select a valid encrypted file with the .sunako extension.",
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
            decryptorResultContainer,
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

// For hiding the secret
const hideSecretForm = document.getElementById("hide-secret-form");
const typeSelector = hideSecretForm.type_selector;
const secretMessageContainer = document.getElementById(
    "secret-message-container",
);
const hideSecretSubmitBtn = document.getElementById("hide_submit_btn");
const hideSecretSubmitBtnIndicator = hideSecretSubmitBtn.querySelector(
    ".button-progress-indicator",
);

const secretFileContainer = document.getElementById("secret-file-container");
const secretFileChooser = document.getElementById("secret-file-chooser");
const secretFileInput = hideSecretForm.secret_file_input;
const secretFileInputBtn = document.getElementById("secret-file-select-btn");
const secretFileInfo = document.getElementById("secret-file-info");

const mediaCarrierChooser = document.getElementById("media-carrier-chooser");
const mediaCarrierInput = hideSecretForm.media_carrier_input;
const mediaCarrierInputBtn = document.getElementById(
    "media-carrier-select-btn",
);
const mediaCarrierInfo = document.getElementById("media-carrier-info");

const enableEncryptionCheckbox = hideSecretForm.enable_encryption;
const encryptSecretPassField = document.getElementById(
    "encrypt-secret-pass-field",
);

const encodeResult = document.getElementById("stego-encode-result");
const encodeResultContainer = document.getElementById(
    "encode-result-container",
);

const stegoEncodeAPI = "/api/steganography/hide";
let secretType = "text";
let enableEncryptionState = false;
let accumulatedSecretFile = new DataTransfer();
let accumulatedMediaCarrier = new DataTransfer();

// Type selection listener
typeSelector.addEventListener("change", () => {
    secretMessageContainer.classList.add("hidden");
    secretFileContainer.classList.add("hidden");

    hideSupportText(hideSecretForm.secret_message);
    hideSupportText(hideSecretForm.secret_password);

    // Reset secret message state
    hideSecretForm.secret_message.value = "";

    if (typeSelector.value === "plain-text") {
        secretType = "text";

        hideSecretForm.secret_message.required = true;
        secretMessageContainer.classList.remove("hidden");
    } else {
        secretType = "file";

        hideSecretForm.secret_message.required = false;
        secretFileContainer.classList.remove("hidden");
    }
});

// Secret file handler
secretFileInputBtn.addEventListener("click", () => secretFileInput.click());
secretFileInput.addEventListener("change", () => {
    // Merge new selections into accumulated list
    Array.from(secretFileInput.files).forEach((file) => {
        accumulatedSecretFile.items.add(file);
    });

    // Update the input element's files
    secretFileInput.files = accumulatedSecretFile.files;

    // Render accumulated list
    renderFileInputList(
        secretFileInfo,
        secretFileInput,
        secretFileChooser,
        (updatedFiles) => {
            // Sync DataTransfer when items are deleted via close button
            accumulatedSecretFile = new DataTransfer();
            Array.from(updatedFiles).forEach((f) =>
                accumulatedSecretFile.items.add(f),
            );
        },
    );
});

// Media carrier handler
mediaCarrierInputBtn.addEventListener("click", () => mediaCarrierInput.click());
mediaCarrierInput.addEventListener("change", () => {
    // Merge new selections into accumulated list
    Array.from(mediaCarrierInput.files).forEach((file) => {
        accumulatedMediaCarrier.items.add(file);
    });

    // Update the input element's files
    mediaCarrierInput.files = accumulatedMediaCarrier.files;

    // Render accumulated list
    renderFileInputList(
        mediaCarrierInfo,
        mediaCarrierInput,
        mediaCarrierChooser,
        (updatedFiles) => {
            // Sync DataTransfer when items are deleted via close button
            accumulatedMediaCarrier = new DataTransfer();
            Array.from(updatedFiles).forEach((f) =>
                accumulatedMediaCarrier.items.add(f),
            );
        },
    );
});

// Security settings
// Enable encryption
function enableEncryption() {
    // Setting the timeout for fixing stupid bug checkbox checked issue
    setTimeout(() => {
        if (hideSecretForm.enable_encryption.checked) {
            encryptSecretPassField.classList.remove("hidden");
            hideSecretForm.secret_password.required = true;

            enableEncryptionState = true;
        } else {
            encryptSecretPassField.classList.add("hidden");
            hideSecretForm.secret_password.required = false;

            enableEncryptionState = false;
        }
    }, 50);
}

enableEncryptionCheckbox.addEventListener("click", enableEncryption);

// Start the encode
function stegoEncode() {
    // Check media carrier
    if (!mediaCarrierInput.files[0]) {
        showAlert(
            "Unable to process file",
            "No file has been provided for hiding the secret. Please ensure you select a file to hide the secret.",
        );

        hideSecretSubmitBtnIndicator.classList.add("hidden!");
        return;
    }

    // Progress circle
    const circularProgress = hideSecretSubmitBtnIndicator.querySelector(
        "md-circular-progress",
    );

    // Form data for hiding secret
    const formData = new FormData();
    formData.append("secret_type", secretType);
    formData.append("media_carrier", mediaCarrierInput.files[0]);

    // Check secret type
    if (secretType === "text") {
        formData.append("secret_message", hideSecretForm.secret_message.value);
    } else {
        if (!secretFileInput.files[0]) {
            showAlert(
                "Unable to process file",
                "No files have been provided to hide. Make sure you select the files you want to hide.",
            );

            hideSecretSubmitBtnIndicator.classList.add("hidden!");
            return;
        } else {
            formData.append("secret_file_input", secretFileInput.files[0]);
        }
    }

    // Is encryption enabled?
    if (enableEncryptionState) {
        formData.append(
            "secret_password",
            hideSecretForm.secret_password.value,
        );
    }

    // clear previous download url
    encodeResult.classList.add("hidden");
    clearResultFileInfo(encodeResultContainer);

    // Send the data to server
    const xhr = new XMLHttpRequest();
    xhr.open("POST", stegoEncodeAPI, true);

    xhr.responseType = "blob";

    xhr.upload.onprogress = (e) => {
        if (e.lengthComputable) {
            const percentComplete = (e.loaded / e.total) * 100;
            circularProgress.removeAttribute("indeterminate");
            circularProgress.setAttribute("value", percentComplete / 100);
        }
    };

    xhr.upload.onload = () => {
        circularProgress.removeAttribute("value");
        circularProgress.setAttribute("indeterminate", "");
    };

    xhr.onload = () => {
        if (xhr.status === 200) {
            let downloadName = mediaCarrierInput.files[0].name; // Fallback
            const disposition = xhr.getResponseHeader("Content-Disposition");

            if (disposition) {
                const utf8Matches = /filename\*=UTF-8''([^;\n]*)/i.exec(
                    disposition,
                );

                if (utf8Matches && utf8Matches[1]) {
                    downloadName = decodeURIComponent(utf8Matches[1]);
                } else {
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

            // Attach to the Download button
            renderResultFileInfo(encodeResultContainer, blob, downloadName);
            encodeResult.classList.remove("hidden");

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
        hideSecretSubmitBtnIndicator.classList.add("hidden!");
        circularProgress.value = 0;
    }
}

hideSecretForm.addEventListener("submit", (event) => {
    event.preventDefault();

    if (hideSecretSubmitBtnIndicator.classList.contains("hidden!")) {
        hideSecretSubmitBtnIndicator.classList.remove("hidden!");

        hideSupportText(hideSecretForm.secret_message);
        hideSupportText(hideSecretForm.secret_password);

        stegoEncode();
    }
});

// ========== For reveal the secret ==========
// File inspection
async function inspectStegoFile(file) {
    if (!file) return { hasSecret: false, isEncrypted: false };

    // Read the file as an ArrayBuffer
    const buffer = await file.arrayBuffer();
    const bytes = new Uint8Array(buffer);

    // Magic Bytes "SNK1" in ASCII decimal values: [83, 78, 75, 49]
    const magic = [83, 78, 75, 49];
    let magicIdx = -1;

    // Search for "SNK1" from the back of the file
    for (let i = bytes.length - 4; i >= 0; i--) {
        if (
            bytes[i] === magic[0] &&
            bytes[i + 1] === magic[1] &&
            bytes[i + 2] === magic[2] &&
            bytes[i + 3] === magic[3]
        ) {
            magicIdx = i;
            break;
        }
    }

    // No SNK1 header found
    if (magicIdx === -1) {
        return { hasSecret: false, isEncrypted: false };
    }

    // Read the encryption flag byte right after SNK1
    const flagIdx = magicIdx + 4;
    const isEncrypted = bytes[flagIdx] === 0x01;

    return { hasSecret: true, isEncrypted: isEncrypted };
}

const decoderFileForm = document.getElementById("reveal-secret-form");
const decoderBrowseBtn = document.getElementById("reveal-secret-browse-btn");
const decoderFileInput = document.getElementById("reveal_secret_file_input");
const decoderDropZone = document.getElementById("reveal-secret-drop-zone");
const decoderDropZoneLoadingLayer =
    decoderDropZone.querySelector(".loading-layer");
const decoderFileInfo = document.getElementById("reveal-secret-file-info");

const decoderNextStep = document.getElementById("reveal-secret-next-step");
const decoderPasswordElm = document.getElementById("decoder-password");
const decoderButton = document.getElementById("decode_submit_btn");
const decoderProgressIndicator = decoderButton.querySelector(
    ".button-progress-indicator",
);

const decodeResultContainer = document.getElementById(
    "decode-result-container",
);

const stegoDecodeAPI = "/api/steganography/reveal";
let encryptedSecret = false;
let accumulatedDecodeFile = new DataTransfer();

// Native trigger
decoderBrowseBtn.addEventListener("click", () => decoderFileInput.click());
decoderFileInput.addEventListener("change", async () => {
    decoderDropZoneLoadingLayer.classList.remove("hidden");

    // Check if the file has secret
    const result = await inspectStegoFile(decoderFileInput.files[0]);

    if (!result.hasSecret) {
        showAlert(
            "No hidden secret found",
            "No hidden secret detected in this file.",
        );

        decoderDropZoneLoadingLayer.classList.add("hidden");
    } else {
        decoderDropZoneLoadingLayer.classList.add("hidden");

        // Merge new selections into accumulated list
        Array.from(decoderFileInput.files).forEach((file) => {
            accumulatedDecodeFile.items.add(file);
        });

        // Update the input element's files
        decoderFileInput.files = accumulatedDecodeFile.files;

        // Render accumulated list
        renderFileInputList(
            decoderFileInfo,
            decoderFileInput,
            decoderDropZone,
            (updatedFiles) => {
                // Sync DataTransfer when items are deleted via close button
                accumulatedDecodeFile = new DataTransfer();
                Array.from(updatedFiles).forEach((f) =>
                    accumulatedDecodeFile.items.add(f),
                );
            },
            decoderNextStep,
            decodeResultContainer,
        );

        if (result.isEncrypted) {
            decoderPasswordElm.classList.remove("hidden");
            decoderFileForm.decode_key.required = true;

            encryptedSecret = true;
        } else {
            decoderPasswordElm.classList.add("hidden");
            decoderFileForm.decode_key.required = false;

            encryptedSecret = false;
        }
    }
});

// Drag-and-drop handles
decoderDropZone.addEventListener("dragover", (e) => {
    e.preventDefault();
    decoderDropZone.classList.add("drag-over");
});

decoderDropZone.addEventListener("dragleave", () => {
    decoderDropZone.classList.remove("drag-over");
});

decoderDropZone.addEventListener("drop", async (e) => {
    e.preventDefault();
    decoderDropZone.classList.remove("drag-over");

    if (e.dataTransfer.files.length > 0) {
        const droppedFile = e.dataTransfer.files[0];
        const extension = droppedFile.name.split(".").pop().toLowerCase();

        decoderFileInput.files = e.dataTransfer.files;
        decoderDropZoneLoadingLayer.classList.remove("hidden");

        // Check if the file has secret
        const result = await inspectStegoFile(droppedFile);

        if (!result.hasSecret) {
            showAlert(
                "No hidden secret found",
                "No hidden secret detected in this file.",
            );

            decoderDropZoneLoadingLayer.classList.add("hidden");
        } else {
            decoderDropZoneLoadingLayer.classList.add("hidden");

            // Merge new selections into accumulated list
            Array.from(decoderFileInput.files).forEach((file) => {
                accumulatedDecodeFile.items.add(file);
            });

            // Update the input element's files
            decoderFileInput.files = accumulatedDecodeFile.files;

            // Render accumulated list
            renderFileInputList(
                decoderFileInfo,
                decoderFileInput,
                decoderDropZone,
                (updatedFiles) => {
                    // Sync DataTransfer when items are deleted via close button
                    accumulatedDecodeFile = new DataTransfer();
                    Array.from(updatedFiles).forEach((f) =>
                        accumulatedDecodeFile.items.add(f),
                    );
                },
                decoderNextStep,
                decodeResultContainer,
            );

            if (result.isEncrypted) {
                decoderPasswordElm.classList.remove("hidden");
                decoderFileForm.decode_key.required = true;

                encryptedSecret = true;
            } else {
                decoderPasswordElm.classList.add("hidden");
                decoderFileForm.decode_key.required = false;

                encryptedSecret = false;
            }
        }
    }
});

// Start the decode
function stegoDecode() {
    // Check media carrier
    if (!decoderFileInput.files[0]) {
        showAlert(
            "Unable to process file",
            "No file has been provided to reveal its secrets.",
        );

        decoderProgressIndicator.classList.add("hidden!");
        return;
    }

    // Progress circle
    const circularProgress = decoderProgressIndicator.querySelector(
        "md-circular-progress",
    );

    // Form data for revealing secret
    const formData = new FormData();
    formData.append("media_carrier_input", decoderFileInput.files[0]);

    // Is it encrypted?
    if (encryptedSecret) {
        formData.append("secret_password", decoderFileForm.decode_key.value);
    }

    // clear previous download url
    clearResultFileInfo(decodeResultContainer);

    // Send the data to server
    const xhr = new XMLHttpRequest();
    xhr.open("POST", stegoDecodeAPI, true);

    xhr.responseType = "blob";

    xhr.upload.onprogress = (e) => {
        if (e.lengthComputable) {
            const percentComplete = (e.loaded / e.total) * 100;
            circularProgress.removeAttribute("indeterminate");
            circularProgress.setAttribute("value", percentComplete / 100);
        }
    };

    xhr.upload.onload = () => {
        circularProgress.removeAttribute("value");
        circularProgress.setAttribute("indeterminate", "");
    };

    xhr.onload = () => {
        const contentType = xhr.getResponseHeader("Content-Type") || "";

        if (xhr.status === 200 && !contentType.includes("application/json")) {
            let downloadName = decoderFileInput.files[0].name; // Fallback
            const disposition = xhr.getResponseHeader("Content-Disposition");

            if (disposition) {
                const utf8Matches = /filename\*=UTF-8''([^;\n]*)/i.exec(
                    disposition,
                );
                if (utf8Matches && utf8Matches[1]) {
                    downloadName = decodeURIComponent(utf8Matches[1]);
                } else {
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
            renderResultFileInfo(decodeResultContainer, blob, downloadName);

            // Success feedback
            showSnackbar("The process was successfully completed.");
            resetUploadButton();
        }

        if (contentType.includes("application/json")) {
            // Handle JSON response
            const reader = new FileReader();
            reader.onload = function () {
                try {
                    const responseJson = JSON.parse(reader.result);
                    let errorMessage;

                    if (
                        xhr.status === 200 &&
                        responseJson.status === "success"
                    ) {
                        // Success: Extracted plain text secret
                        renderResultText(
                            decodeResultContainer,
                            responseJson.data.content,
                        );
                    } else if (
                        xhr.status === 401 &&
                        responseJson.data &&
                        responseJson.data.is_locked
                    ) {
                        // Password Required Error
                        errorMessage = responseJson.message;

                        showSupportText(
                            decoderFileForm.decode_key,
                            errorMessage,
                        );
                    } else {
                        // Standard Error
                        errorMessage =
                            responseJson.message ||
                            "An unknown error occurred. Please try again";

                        showAlert("Unable to process file", errorMessage);
                    }
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
        decoderProgressIndicator.classList.add("hidden!");
        circularProgress.value = 0;
    }
}

decoderFileForm.addEventListener("submit", (event) => {
    event.preventDefault();

    if (decoderProgressIndicator.classList.contains("hidden!")) {
        decoderProgressIndicator.classList.remove("hidden!");

        stegoDecode();
    }
});
