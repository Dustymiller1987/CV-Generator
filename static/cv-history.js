(() => {
    const storageKey = "cv-generator.saved-cvs.v1";
    const fieldNames = [
        "theme",
        "name",
        "email",
        "phone",
        "location",
        "linkedin",
        "git_profile",
        "education",
        "experience",
        "skills",
        "certification",
        "hobbies",
        "job_title",
    ];

    function readSavedCvs() {
        const stored = window.localStorage.getItem(storageKey);
        if (stored === null) {
            return [];
        }

        const records = JSON.parse(stored);
        if (
            !Array.isArray(records) ||
            records.some(
                (record) =>
                    !record ||
                    typeof record.id !== "string" ||
                    typeof record.savedAt !== "string" ||
                    !record.values ||
                    typeof record.values !== "object"
            )
        ) {
            throw new Error("Saved CV data is invalid. Remove it from browser storage to continue.");
        }

        return records;
    }

    function writeSavedCvs(records) {
        window.localStorage.setItem(storageKey, JSON.stringify(records));
    }

    function setStatus(element, message, isError = false) {
        if (!element) {
            return;
        }
        element.textContent = message;
        element.classList.toggle("is-error", isError);
    }

    function createHiddenInput(name, value) {
        const input = document.createElement("input");
        input.type = "hidden";
        input.name = name;
        input.value = value;
        return input;
    }

    function reopenCv(record, action) {
        const form = document.createElement("form");
        form.method = "post";
        form.action = action;
        for (const name of fieldNames) {
            const value = record.values[name];
            if (typeof value !== "string" && !["hobbies", "job_title"].includes(name)) {
                throw new Error("This saved CV is missing required information.");
            }
            form.append(createHiddenInput(name, typeof value === "string" ? value : ""));
        }
        document.body.append(form);
        form.submit();
    }

    function renderSavedCvs(section, list, status) {
        try {
            const records = readSavedCvs();
            list.replaceChildren();
            section.hidden = records.length === 0;

            for (const record of records) {
                const item = document.createElement("li");
                item.className = "saved-cv-item";

                const details = document.createElement("div");
                const title = document.createElement("strong");
                title.textContent = record.values.name || "Untitled CV";
                const savedDate = document.createElement("p");
                const date = new Date(record.savedAt);
                savedDate.textContent = Number.isNaN(date.getTime())
                    ? "Saved date unavailable"
                    : `Saved ${date.toLocaleString()}`;
                details.append(title, savedDate);

                const actions = document.createElement("div");
                actions.className = "saved-cv-item-actions";
                const openButton = document.createElement("button");
                openButton.type = "button";
                openButton.textContent = "Open CV";
                openButton.dataset.action = "open";
                openButton.dataset.id = record.id;
                const deleteButton = document.createElement("button");
                deleteButton.type = "button";
                deleteButton.textContent = "Delete";
                deleteButton.className = "delete-saved-cv";
                deleteButton.dataset.action = "delete";
                deleteButton.dataset.id = record.id;
                actions.append(openButton, deleteButton);
                item.append(details, actions);
                list.append(item);
            }

            setStatus(status, "");
        } catch (error) {
            section.hidden = false;
            setStatus(status, `Could not load saved CVs: ${error.message}`, true);
        }
    }

    const saveButton = document.getElementById("save-cv-button");
    if (saveButton) {
        const form = document.getElementById("cv-data-form");
        const status = document.getElementById("save-cv-status");
        saveButton.addEventListener("click", () => {
            try {
                const values = Object.fromEntries(new FormData(form).entries());
                const record = {
                    id: `${Date.now()}-${Math.random().toString(16).slice(2)}`,
                    savedAt: new Date().toISOString(),
                    values,
                };
                writeSavedCvs([record, ...readSavedCvs()]);
                setStatus(status, "CV saved in this browser.");
            } catch (error) {
                setStatus(status, `Could not save CV: ${error.message}`, true);
            }
        });
    }

    const section = document.getElementById("saved-cvs");
    const list = document.getElementById("saved-cv-list");
    const status = document.getElementById("saved-cvs-status");
    if (section && list) {
        renderSavedCvs(section, list, status);
        list.addEventListener("click", (event) => {
            const button = event.target.closest("button[data-action]");
            if (!button) {
                return;
            }

            try {
                const records = readSavedCvs();
                const record = records.find((item) => item.id === button.dataset.id);
                if (!record) {
                    throw new Error("The selected saved CV could not be found.");
                }

                if (button.dataset.action === "open") {
                    reopenCv(record, section.dataset.generateUrl);
                    return;
                }

                if (button.dataset.action === "delete") {
                    writeSavedCvs(records.filter((item) => item.id !== record.id));
                    renderSavedCvs(section, list, status);
                }
            } catch (error) {
                setStatus(status, `Could not update saved CVs: ${error.message}`, true);
            }
        });
    }
})();
