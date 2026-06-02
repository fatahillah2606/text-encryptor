// Send request
function sendRequest(apiURI, data = null, methodType = "GET") {
    // Set request init
    const requestInit = {
        method: methodType,
        headers: { "Content-Type": "application/json" },
    };

    // If method is POST or PUT, attach the body
    if (methodType !== "GET" && methodType !== "DELETE" && data) {
        requestInit.body = JSON.stringify(data);
    }

    // Send request
    return fetch(apiURI, requestInit).then(async (response) => {
        const data = await response.json();

        if (!response.ok) {
            return Promise.reject(data);
        }
        return data;
    });
}
