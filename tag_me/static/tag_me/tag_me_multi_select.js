// original code by https://github.com/alexpechkarev/alpinejs-multiselect/
//function monitorEscapeKeyAndListeners() {
//    window.addEventListener('keydown', (event) => {
//        console.log('ESCAPE LISTENER')
//        if (event.key === 'Escape') {
//            event.preventDefault(); // Prevent default behavior
//
//            let currentElement = event.target;
//            const listenerChain = []; 
//
//            while (currentElement) {
//                const listeners = getEventListeners(currentElement);
//                if (listeners && listeners.keydown) {
//                    const escapeListeners = listeners.keydown.filter(listener => 
//                        listener.listener && 
//                            listener.listener.toString().includes('event.key === \'Escape\'')
//                    );
//                    if (escapeListeners.length > 0) {
//                        listenerChain.push({
//                            element: currentElement,
//                            listeners: escapeListeners
//                        });
//                    }
//                }
//                currentElement = currentElement.parentElement;
//            }
//
//            console.log('Escape key pressed! Listener chain:', listenerChain);
//        }
//    });
//}

function base64Encode(obj) {
    return btoa(JSON.stringify(obj));
}

document.addEventListener("alpine:init", () => {
    function createOptionElementFromTag(selectElement, tag) {
        // DEPRECATED
        // Find a way to add tags directly to alpineTagMeMultiSelect
        // instead of creating <option> elements first
        let addTag = String(tag).trim()
        const option = document.createElement('option');
        option.setAttribute('data-search', addTag);
        option.setAttribute('value', addTag);
        option.innerText = addTag;

        selectElement.appendChild(option);
    }
    Alpine.data("alpineTagMeMultiSelect", (obj) => ({
        addTagURL: obj.addTagURL,
        elementId: obj.elementId,
        permittedToAddTags: obj.permittedToAddTags,
        allowMultipleSelect: obj.allowMultipleSelect,
        selected: obj.selected,
        canAddNewTag: false,
        autoSelectNewTags: obj.autoSelectNewTags,
        newTagsArray: [],
        options: [],
        selectedElms: [],
        show: false,
        menuShow: false,
        search: '',
        open() {
            this.show = true
        },
        close() {
            this.show = false
        },
        toggle() {
            this.show = !this.show
        },
        isOpen() {
            return this.show === true
        },
        menuOpen() {
            this.menuShow = true
        },
        menuClose() {
            this.menuShow = false;
            //setTimeout(() => {
            //    this.menuShow = false; 
            //}, 100); // 100 milliseconds delay
        },
        menuToggle() {
            this.menuShow = !this.menuShow
        },
        menuIsOpen() {
            return this.menuShow === true
        },

        logOptions() {
            console.log("Current Options Container:", this.options);
        },

        // Initializing component
        init() {
            const options = document.getElementById(this.elementId).options;
            for (let i = 0; i < options.length; i++) {

                this.options.push({
                    value: options[i].value,
                    text: options[i].innerText,
                    search: options[i].dataset.search,
                    selected: Object.values(this.selected).includes(options[i].value)
                });

                if (this.options[i].selected) {
                    this.selectedElms.push(this.options[i])
                }
            }

            // searching for the given value
            this.$watch("search", (e => {
                const options = document.getElementById(this.elementId).options;
                this.options = Object.values(options).filter((el) => {
                    var reg = new RegExp(this.search, 'gi');
                    return el.dataset.search.match(reg)
                }).map((el) => {
                        return {
                            value: el.value,
                            text: el.innerText,
                            search: el.dataset.search,
                            selected: Object.values(this.selected).includes(el.value)
                        };
                    });
                this.canAddNewTag = this.options.length === 0;
            }));
        },
        createNewTag() {
            this.canAddNewTag = false; // Remove 'add' button when new tag has been submitted
            const selectElement = document.getElementById(this.elementId);
            this.newTagsArray.length = 0;
            this.newTagsArray = this.search.split(',').map(tag => String(tag).trim());
            fetch(this.addTagURL, {
                method: 'POST',
                body: new URLSearchParams([
                    ['encoded_tag', base64Encode(this.search)],
                    ['csrfmiddlewaretoken', getCookie('csrftoken')],
                ]),
            })
                .then(r => r.status === 200 ? r.json() : { is_error: true, error_status: r.status_code, response: r })
                .then(data => {
                    console.log('THE DATA IS', data);
                    if (data.is_error) {
                        console.log(data.response);
                        console.error(`Did not expect HTTP status code when creating tag: ${data.error_status}.`);
                    } else {
                        selectElement.innerHTML = ''; // Remove all options in select element
                        data.tags.forEach(tag => {
                            // Repopulate select element with options from tags
                            createOptionElementFromTag(selectElement, tag);
                        });

                        this.clearSearch(); // Clear search input
                    }
                });
        },
        // clear search field
        clearSearch() {
            this.search = ''
        },
        // deselect selected options
        deselectTag() {
            setTimeout(() => {
                this.selected = []
                this.selectedElms = []
                Object.keys(this.options).forEach((key) => {
                    this.options[key].selected = false;
                })
            }, 100)
        },
        // select given option
        select(index, event) {
            if (!this.allowMultipleSelect && this.selected.length === 1 ) {
                alert("You've reached the maximum number of selections!");
                return;
            }
            if (!this.options[index].selected) {
                this.options[index].selected = true;
                this.options[index].element = event.target;
                this.selected.push(this.options[index].value);
                this.selectedElms.push(this.options[index]);

            } else {
                this.selected.splice(this.selected.lastIndexOf(index), 1);
                this.options[index].selected = false
                Object.keys(this.selectedElms).forEach((key) => {
                    if (this.selectedElms[key].value == this.options[index].value) {
                        setTimeout(() => {
                            this.selectedElms.splice(key, 1)
                        }, 100)
                    }
                })
            }
        },
        // remove from selected option
        remove(index, option) {
            this.selectedElms.splice(index, 1);
            Object.keys(this.options).forEach((key) => {
                if (this.options[key].value == option.value) {
                    this.options[key].selected = false;
                    Object.keys(this.selected).forEach((skey) => {
                        if (this.selected[skey] == option.value) {
                            this.selected.splice(skey, 1);
                        }
                    })
                }
            })
        },
        // filter out selected elements
        selectedElements() {
            return this.options.filter(op => op.selected === true)
        },
        // get selected values
        selectedValues() {
            return this.options.filter(op => op.selected === true).map(el => el.value)
        }
    }));
});
