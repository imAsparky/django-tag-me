// code by https://github.com/alexpechkarev/alpinejs-multiselect/
function base64Encode(obj) {
    return btoa(JSON.stringify(obj));
}
document.addEventListener("alpine:init", () => {
    function createOptionElementFromTag(selectElement, tag) {
      // DEPRECATED
      // Find a way to add tags directly to alpineTagMeMultiSelect
      // instead of creatingn <option> elements first
      const option = document.createElement('option');
      option.setAttribute('data-search', tag)
      option.setAttribute('value', tag)
      option.innerText = tag;

      selectElement.appendChild(option);
    }
    Alpine.data("alpineTagMeMultiSelect", (obj) => ({
        addTagURL: obj.addTagURL,
        elementId: obj.elementId,
        selected: obj.selected,
        canAddNewTag: false,
        options: [],
        selectedElms: [],
        show: false,
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
          this.canAddNewTag = false; // Remove 'add' button on clicking of 'add' button

          const selectElement = document.getElementById(this.elementId);
          fetch(this.addTagURL, {
            method: 'POST',
            body: new URLSearchParams([
              ['encoded_tag', base64Encode(this.search)],
              ['csrfmiddlewaretoken', getCookie('csrftoken')],
            ]),
          })
            .then(r => r.status === 200 ? r.json() : { is_error: true, error_status: r.status_code, response: r })
            .then(data => {
              if (data.is_error) {
                console.log(data.response);
                console.error(`Did not expect HTTP status code when creating tag: ${data.error_status}.`);
              } else {
                selectElement.innerHTML = ''; // Remove all options in select element
                data.tags.forEach(tag =>
                  // Repopulate select element with options from tags
                  createOptionElementFromTag(selectElement, tag));

                this.clear(); // Clear search input
              }
            });
        },
        // clear search field
        clear() {
            this.search = ''
        },
        // deselect selected options
        deselect() {
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
