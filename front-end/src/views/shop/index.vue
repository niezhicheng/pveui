<template>
  <div class="shop-page">
    <div class="shop-header">
      <div class="header-content">
        <div class="header-left">
          <icon-gift :size="32" />
          <a-typography-title :heading="4" style="margin: 0 0 0 12px">发卡商城</a-typography-title>
        </div>
        <a-typography-text type="secondary">安全便捷的虚拟商品购买平台</a-typography-text>
      </div>
    </div>

    <div class="shop-content">
      <a-spin :loading="loading" style="width: 100%">
        <a-empty v-if="!loading && products.length === 0" description="暂无商品" />
        <a-grid v-else :cols="{ xs: 1, sm: 2, md: 3, lg: 4 }" :col-gap="20" :row-gap="20">
          <a-grid-item v-for="item in products" :key="item.id">
            <a-card class="product-card" :bordered="true" hoverable>
              <template #cover>
                <div class="product-cover">
                  <div class="cover-icon">
                    <icon-gift :size="56" />
                  </div>
                  <a-tag v-if="item.stock > 0" color="green" class="stock-tag">库存 {{ item.stock }}</a-tag>
                  <a-tag v-else color="red" class="stock-tag">缺货</a-tag>
                </div>
              </template>
              <div class="product-body">
                <a-typography-title :heading="6" style="margin: 0 0 8px">{{ item.name }}</a-typography-title>
                <a-typography-paragraph :ellipsis="{ rows: 2 }" type="secondary" style="margin: 0 0 16px; min-height: 44px">
                  {{ item.description || '暂无描述' }}
                </a-typography-paragraph>
                <a-divider :margin="12" />
                <div class="product-footer">
                  <div class="price-section">
                    <a-statistic
                      :value="Number(item.price)"
                      :precision="2"
                      prefix="¥"
                      :value-style="{ color: '#165DFF', fontSize: '24px', fontWeight: 600 }"
                    />
                  </div>
                  <a-button type="primary" :disabled="item.stock === 0" @click="handleBuy(item)">
                    <template #icon><icon-plus /></template>
                    立即购买
                  </a-button>
                </div>
              </div>
            </a-card>
          </a-grid-item>
        </a-grid>
      </a-spin>
    </div>

    <!-- 购买对话框 -->
    <a-modal
      v-model:visible="buyVisible"
      title="购买商品"
      :width="520"
      @ok="handleConfirmBuy"
      @cancel="handleCancelBuy"
    >
      <div v-if="currentProduct">
        <a-descriptions :column="1" bordered size="large">
          <a-descriptions-item label="商品名称">
            <a-typography-text strong>{{ currentProduct.name }}</a-typography-text>
          </a-descriptions-item>
          <a-descriptions-item label="商品描述">
            {{ currentProduct.description || '-' }}
          </a-descriptions-item>
          <a-descriptions-item label="单价">
            <a-statistic
              :value="Number(currentProduct.price)"
              :precision="2"
              prefix="¥"
              :value-style="{ color: '#165DFF', fontSize: '18px' }"
            />
          </a-descriptions-item>
          <a-descriptions-item label="库存">
            <a-tag :color="currentProduct.stock > 0 ? 'green' : 'red'">
              {{ currentProduct.stock > 0 ? `剩余 ${currentProduct.stock} 件` : '缺货' }}
            </a-tag>
          </a-descriptions-item>
        </a-descriptions>

        <a-divider />

        <a-form :model="buyForm" layout="vertical" style="margin-top: 16px">
          <a-form-item label="购买数量" field="quantity">
            <a-input-number
              v-model="buyQuantity"
              :min="1"
              :max="Math.min(10, currentProduct.stock)"
              style="width: 100%"
            />
          </a-form-item>
          <a-form-item label="总价">
            <a-statistic
              :value="Number((Number(currentProduct.price) * buyQuantity).toFixed(2))"
              :precision="2"
              prefix="¥"
              :value-style="{ color: '#F53F3F', fontSize: '20px', fontWeight: 600 }"
            />
          </a-form-item>
          <a-form-item label="联系方式" field="contact" required>
            <a-input v-model="contactInfo" placeholder="QQ/微信/邮箱" allow-clear />
          </a-form-item>
          <a-form-item label="备注" field="remark">
            <a-textarea v-model="buyRemark" placeholder="选填" :rows="3" allow-clear />
          </a-form-item>
        </a-form>
      </div>
    </a-modal>

    <!-- 订单结果对话框 -->
    <a-modal
      v-model:visible="resultVisible"
      title="订单信息"
      :footer="false"
      :width="640"
      :mask-closable="false"
    >
      <div v-if="orderResult">
        <a-result
          :status="orderResult.success ? 'success' : 'error'"
          :title="orderResult.success ? '订单创建成功' : '订单创建失败'"
          :subtitle="orderResult.message"
        >
          <template v-if="orderResult.success && orderResult.data" #extra>
            <a-card :bordered="true" style="margin-top: 24px">
              <a-descriptions :column="1" bordered size="large">
                <a-descriptions-item label="订单号">
                  <a-typography-text copyable strong>{{ orderResult.data.order_no }}</a-typography-text>
                </a-descriptions-item>
                <a-descriptions-item label="商品名称">{{ orderResult.data.product_name }}</a-descriptions-item>
                <a-descriptions-item label="购买数量">{{ orderResult.data.quantity }}</a-descriptions-item>
                <a-descriptions-item label="总价">
                  <a-statistic
                    :value="Number(orderResult.data.total_price)"
                    :precision="2"
                    prefix="¥"
                    :value-style="{ color: '#165DFF', fontSize: '18px' }"
                  />
                </a-descriptions-item>
                <a-descriptions-item label="卡密信息">
                  <a-alert type="success" style="margin-top: 8px">
                    <template #icon><icon-check-circle /></template>
                    <div v-for="(card, idx) in orderResult.data.cards" :key="idx" style="margin: 8px 0; font-family: monospace">
                      <a-typography-text copyable>{{ card }}</a-typography-text>
                    </div>
                  </a-alert>
                  <a-typography-text type="secondary" style="display: block; margin-top: 8px; font-size: 12px">
                    💡 请妥善保管卡密信息，建议复制保存
                  </a-typography-text>
                </a-descriptions-item>
              </a-descriptions>
            </a-card>
            <a-space style="margin-top: 24px; width: 100%; justify-content: center">
              <a-button type="primary" size="large" @click="resultVisible = false">我知道了</a-button>
            </a-space>
          </template>
        </a-result>
      </div>
    </a-modal>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { Message } from '@arco-design/web-vue'
import { IconGift, IconPlus, IconCheckCircle } from '@arco-design/web-vue/es/icon'
import { getProducts, createOrder } from '@/api/shop'

const loading = ref(false)
const products = ref([])
const buyVisible = ref(false)
const resultVisible = ref(false)
const currentProduct = ref(null)
const buyQuantity = ref(1)
const contactInfo = ref('')
const buyRemark = ref('')
const orderResult = ref(null)
const buyForm = ref({})

async function loadProducts() {
  loading.value = true
  try {
    const res = await getProducts()
    products.value = res.data || res || []
  } catch (e) {
    Message.error('加载商品失败：' + (e.message || '未知错误'))
    products.value = []
  } finally {
    loading.value = false
  }
}

function handleBuy(product) {
  currentProduct.value = product
  buyQuantity.value = 1
  contactInfo.value = ''
  buyRemark.value = ''
  buyVisible.value = true
}

function handleCancelBuy() {
  buyVisible.value = false
  currentProduct.value = null
}

async function handleConfirmBuy() {
  if (!contactInfo.value) {
    Message.warning('请填写联系方式')
    return
  }
  try {
    const res = await createOrder({
      product_id: currentProduct.value.id,
      quantity: buyQuantity.value,
      contact: contactInfo.value,
      remark: buyRemark.value,
    })
    // 后端返回格式：{ success: true, message: "...", data: {...} }
    // res 已经是 response.data，所以直接使用
    if (res.success) {
      orderResult.value = {
        success: true,
        message: res.message || '订单创建成功',
        data: res.data
      }
    } else {
      orderResult.value = {
        success: false,
        message: res.message || '订单创建失败'
      }
    }
    buyVisible.value = false
    resultVisible.value = true
    await loadProducts() // 刷新商品列表
  } catch (e) {
    orderResult.value = {
      success: false,
      message: e.message || '下单失败：未知错误'
    }
    resultVisible.value = true
  }
}

onMounted(loadProducts)
</script>

<style scoped>
.shop-page {
  min-height: 100vh;
  width: 100%;
  background: var(--color-bg-1);
  display: flex;
  flex-direction: column;
}

.shop-header {
  background: var(--color-bg-2);
  border-bottom: 1px solid var(--color-border);
  padding: 0 24px;
  height: 64px;
  display: flex;
  align-items: center;
  flex-shrink: 0;
}

.header-content {
  width: 100%;
  max-width: 1400px;
  margin: 0 auto;
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.header-left {
  display: flex;
  align-items: center;
  color: var(--color-text-1);
}

.shop-content {
  flex: 1;
  padding: 32px 24px;
  max-width: 1400px;
  width: 100%;
  margin: 0 auto;
  box-sizing: border-box;
}

.product-card {
  height: 100%;
  transition: all 0.3s;
  border-radius: 8px;
  overflow: hidden;
}

.product-card:hover {
  transform: translateY(-4px);
  box-shadow: 0 8px 24px rgba(0, 0, 0, 0.12);
}

.product-cover {
  height: 160px;
  background: linear-gradient(135deg, var(--color-primary-light-1) 0%, var(--color-primary) 100%);
  display: flex;
  align-items: center;
  justify-content: center;
  position: relative;
  color: var(--color-white);
}

.cover-icon {
  opacity: 0.9;
}

.stock-tag {
  position: absolute;
  top: 12px;
  right: 12px;
}

.product-body {
  padding: 16px;
}

.product-footer {
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 12px;
}

.price-section {
  flex: 1;
}
</style>
