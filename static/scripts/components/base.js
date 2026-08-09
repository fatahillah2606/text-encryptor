// ========== Encryption key modal ==========
const keySelectorModal = document.getElementById("key-selector-modal");

const keySelectorForm = document.getElementById("key-selector");
const optionKey = keySelectorForm.option_key;
const dialogContext = document.getElementById("dialog-context");

const userKeysAPI = "/api/user/keys";

// Show/Close key modal
async function openKeyModal() {
    await keySelectorModal.show();
}

async function closeKeyModal() {
    await keySelectorModal.close();
    keySelectorForm.set_key.disabled = true;

    optionKey ? checkEncryptionKey() : "";
}

// Set value of keySelector option
function setKeySelectorValue(targetValue) {
    const availableValues = Array.from(optionKey.options).map(
        (opt) => opt.value,
    );

    // Check if value is available
    if (availableValues.includes(targetValue)) {
        optionKey.value = targetValue;
    } else {
        optionKey.value = "manual";
    }
}

// ========== Check encryption key ==========
async function checkEncryptionKey() {
    let encryptionKey = sessionStorage.getItem("encryption_key");
    if (encryptionKey) {
        encryptionKey = JSON.parse(encryptionKey);

        // Set the key selector value
        if (optionKey) {
            setKeySelectorValue(encryptionKey.key);

            // If the value was manual
            if (optionKey.value == "manual") {
                keySelectorForm.custom_key.value = encryptionKey.key;

                keySelectorForm.generate_key.disabled = false;
                keySelectorForm.custom_key.disabled = false;
            } else {
                keySelectorForm.custom_key.value = encryptionKey.key;

                keySelectorForm.generate_key.disabled = true;
                keySelectorForm.custom_key.disabled = true;
            }
        } else {
            // If no option value (guest mode)
            // Remove encryption key except it was manual
            if (encryptionKey.name !== "manual") {
                sessionStorage.removeItem("encryption_key");

                // recall the function
                checkEncryptionKey();
            } else {
                keySelectorForm.custom_key.value = encryptionKey.key;
            }
        }

        // Change modal context
        dialogContext.textContent =
            "Choose a key to authorize the current session's encryption and decryption tasks.";
    } else {
        try {
            const result = await sendRequest(userKeysAPI, {}, "GET");
            const masterKey = result.data[0];

            saveKeyToSession(masterKey);
            checkEncryptionKey();
        } catch (error) {
            // openKeyModal();

            // Auto generate key for guest mode
            const keyGenerated = await generateKey("#custom_key");
            if (keyGenerated) {
                setEncryptionKey(keySelectorForm.custom_key.value);
            }
        }
    }
}

// ========== Key selector form handler ==========
// Set encryption key
async function changeActiveKey(keyValue, keyName) {
    if (keyValue == "manual") {
        keySelectorForm.generate_key.disabled = false;
        manualKeyForm.classList.remove("hidden");
    } else {
        keyData = {
            name: keyName,
            key: keyValue,
        };

        sessionStorage.setItem("encryption_key", JSON.stringify(keyData));

        showSnackbar("Encryption key changed.");
    }
}

// ========== Option key listener ==========
if (optionKey) {
    optionKey.addEventListener("change", () => {
        // Enable submit key
        keySelectorForm.set_key.disabled = false;

        // Set value of custom key field
        const selectedOption = optionKey.selectedOptions[0];
        if (selectedOption) {
            const value = selectedOption.value;

            if (value !== "manual") {
                keySelectorForm.generate_key.disabled = true;
                keySelectorForm.custom_key.value = value;
            } else {
                keySelectorForm.generate_key.disabled = false;
                keySelectorForm.custom_key.value = "";
            }
        }

        // Check the custom key field
        if (optionKey.value == "manual") {
            // Enable custom key field and generate key button
            keySelectorForm.generate_key.disabled = false;
            keySelectorForm.custom_key.disabled = false;

            // Enable/disable submit key
            if (keySelectorForm.custom_key.value.trim() !== "") {
                keySelectorForm.set_key.disabled = false;
            } else {
                keySelectorForm.set_key.disabled = true;
            }
        } else {
            keySelectorForm.custom_key.disabled = true;
        }
    });
}

// ========== Custom key field ==========
function checkCustomKeyField() {
    if (keySelectorForm.custom_key.value.trim() !== "") {
        keySelectorForm.set_key.disabled = false;
    } else {
        keySelectorForm.set_key.disabled = true;
    }
}

keySelectorForm.custom_key.addEventListener("keyup", () => {
    checkCustomKeyField();
});

// ========== Generate key btn ==========
keySelectorForm.generate_key.addEventListener("click", async () => {
    const keyGenerated = await generateKey("#custom_key");

    if (keyGenerated) {
        keySelectorForm.set_key.disabled = false;
    }
});

// ========== On submit ==========
keySelectorForm.addEventListener("submit", (event) => {
    event.preventDefault();

    if (!keySelectorForm.set_key.disabled) {
        if (optionKey && optionKey.value !== "manual") {
            // Set active key base on choosed option
            const selectedOption = optionKey.selectedOptions[0];

            if (selectedOption) {
                const value = selectedOption.value;
                const customContext =
                    selectedOption.getAttribute("data-context");

                changeActiveKey(value, customContext);
                checkEncryptionKey();
            }
        } else {
            setEncryptionKey(keySelectorForm.custom_key.value);
        }

        closeKeyModal();
    }
});

// Check the encryption key
checkEncryptionKey();
