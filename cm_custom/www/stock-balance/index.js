Vue.component('search-form', {
  template: `
<div class="position-relative">
  <div v-if="!isFieldsVisible">
    <button
      class="btn btn-primary mb-2"
      @click="showFields"
      :disabled="disabled"
    >
      Filter
    </button>
  </div>
  <form v-else @submit.prevent="applyFilters">
    <div class="form-row align-items-center">
      <div class="col-auto">
        <div class="form-group">
          <label for="search" class="sr-only">Search</label>
          <input
            type="text"
            class="form-control"
            id="search"
            name="search"
            placeholder="Item name, description"
            v-model="search"
          />
        </div>
      </div>
      <div class="col-auto">
        <div class="form-group">
          <label for="item_group" class="sr-only">Item Group</label>
          <input
            type="text"
            class="form-control"
            id="item_group"
            name="item_group"
            placeholder="Item Group"
            v-model="item_group"
            @focus="isGroupSelectVisible = true"
          />
        </div>
      </div>
      <div class="col-auto">
        <div class="form-check">
          <input
            class="form-check-input"
            type="checkbox"
            value=""
            id="show_zero"
            v-model="show_zero"
          />
          <label class="form-check-label" for="show_zero">
            Show items with no stock
          </label>
        </div>
      </div>
    </div>
    <ul class="list-group" v-if="isFieldsVisible && isGroupSelectVisible">
      <li
        class="list-group-item"
        style="cursor: pointer;"
        v-for="{ name: group_name } in item_groups"
        :key="name"
        @click.prevent="setItemGroup(group_name)"
      >
        {{ group_name }}
      </li>
    </ul>
    <button type="submit" class="btn btn-primary my-2" :disabled="disabled">
      Apply
    </button>
  </form>
</div>
  `,
  props: ['disabled', 'onApply'],
  data: function () {
    return {
      isFieldsVisible: false,
      item_group: '',
      search: '',
      show_zero: false,
      allItemGroups: [],
      isGroupSelectVisible: false,
    };
  },
  computed: {
    item_groups: function () {
      return this.allItemGroups
        .filter(({ name }) =>
          name.toLowerCase().includes((this.item_group || '').toLowerCase())
        )
        .slice(0, 5);
    },
  },
  methods: {
    showFields() {
      this.isFieldsVisible = true;
    },
    applyFilters() {
      this.isFieldsVisible = false;
      const { item_group, search, show_zero } = this;
      this.onApply({ item_group, search, show_zero });
    },
    setItemGroup(name) {
      this.item_group = name;
      this.isGroupSelectVisible = false;
    },
  },
  async mounted() {
    try {
      const { message } = await frappe.call({
        method: 'list_item_groups',
      });
      this.allItemGroups = message.sort((x, y) => {
        const nameX = x.name.toLowerCase();
        const nameY = y.name.toLowerCase();
        if (nameX < nameY) {
          return -1;
        }

        if (nameX > nameY) {
          return 1;
        }

        return 0;
      });
    } catch (error) {
      console.log(error);
    }
  },
});

var app = new Vue({
  el: '#vue-root',
  template: `
<div>
  <search-form :disabled="isLoading" :onApply="refreshItems" />
  <div class="my-4" v-if="isEmpty">
    <p class="text-muted">No items to show</p>
  </div>
  <div v-else>
    <table class="table">
      <thead>
        <tr>
          <th scope="col">Item Name</th>
          <th scope="col">Item Group</th>
          <th scope="col" class="text-right">Actual</th>
          <th scope="col" class="text-right">Projected</th>
        </tr>
      </thead>
      <tbody>
        <tr v-for="{ item_code, item_name, item_group, actual_qty, projected_qty } in items" :key="item_code">
          <td>{{ item_name }}</td>
          <td>{{ item_group }}</td>
          <td class="text-right">{{ actual_qty }}</td>
          <td class="text-right">{{ projected_qty }}</td>
        </tr>
      </tbody>
    </table>
  </div>
  <div class="spinner-border text-primary my-3" role="status" v-if="isLoading">
    <span class="sr-only">Loading...</span>
  </div>
  <div v-if="hasMore">
    <button
      class="btn btn-default my-2"
      :disabled="isLoading"
      @click="loadMore"
    >
      Load More
    </button>
  </div>
</div>
  `,
  data: function () {
    return {
      items: [],
      isLoading: true,
      hasMore: true,
      requestArgs: {},
    };
  },
  computed: {
    isEmpty: function () {
      return this.items.length === 0;
    },
  },
  methods: {
    refreshItems({ item_group, search, show_zero }) {
      this.requestArgs = {
        item_group,
        search,
        show_zero,
        limit_start: 0,
        limit_page_length: 20,
      };
      this.fetchItems(true);
    },
    loadMore() {
      const { limit_start = 0, limit_page_length = 20 } = this.requestArgs;
      this.requestArgs = {
        ...this.requestArgs,
        limit_start: limit_start + limit_page_length,
      };
      this.fetchItems();
    },
    async fetchItems(isRefresh) {
      try {
        this.isLoading = true;
        const { limit_page_length = 20 } = this.requestArgs;
        const { message: items = [] } = await frappe.call({
          method: 'cm_custom.api.item.stock',
          args: this.requestArgs,
        });
        if (isRefresh) {
          this.items = items;
        } else {
          this.items.push(...items);
        }
        this.hasMore = !(items.length < limit_page_length);
      } catch (error) {
        console.log(error);
      } finally {
        this.isLoading = false;
      }
    },
  },
  mounted() {
    this.fetchItems();
  },
});
