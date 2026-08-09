const decryptProgress = document.getElementById("decrypt-progress");
const expiredQuote = document.getElementById("expired-quote");
const decryptContainer = document.getElementById("decrypt-container");
const decryptResult = document.getElementById("decrypt-result");

window.addEventListener("DOMContentLoaded", async () => {
    // Extract the key from the hash fragment (#)
    const key = window.location.hash.substring(1);
    const blob = "{{ blob }}";

    if (!key) {
        decryptProgress.classList.add("hidden");
        expiredQuote.querySelector("p").textContent =
            "The transmission is fractured. The cryptographic structure doesn't align, meaning the payload or the key has been corrupted. We shouldn't trust this link—let's return to the workspace and verify the source.";

        expiredQuote.classList.remove("hidden");

        showAlert(
            "Unable to decrypt message",
            "The sharing key is missing from the URL. Please double-check the link and try again.",
        );

        return;
    }

    try {
        // Deliver both parts safely via a POST payload
        data = {
            blob: blob,
            key: key,
        };

        const result = await sendRequest(
            "/api/encryptor/decrypt_link",
            data,
            "POST",
        );

        decryptResult.value = result.data;
        decryptContainer.classList.remove("hidden");

        // Remove unnecessary element
        decryptProgress.classList.add("hidden");
        expiredQuote.classList.add("hidden");
    } catch (error) {
        decryptProgress.classList.add("hidden");

        if (error.code === 410) {
            expiredQuote.querySelector("p").textContent =
                "The transmission has faded. The 5-minute security window has passed, and the cryptographic payload has been completely cleared. We should head back to the workstation and regenerate the link if needed.";

            expiredQuote.classList.remove("hidden");
        } else {
            expiredQuote.querySelector("p").textContent =
                "The transmission is fractured. The cryptographic structure doesn't align, meaning the payload or the key has been corrupted. We shouldn't trust this link—let's return to the workspace and verify the source.";

            expiredQuote.classList.remove("hidden");
        }
    }
});
