'use client';

import { useState } from 'react';
import { useQuery, useMutation } from '@tanstack/react-query';

interface Order {
  orderId: string;
  customerName: string;
  trackingCode: string;
  phoneNumber: string;
  status: string;
  shipmentId: string;
}

export default function SMSPage() {
  const [selectedOrders, setSelectedOrders] = useState<string[]>([]);
  const [isDryRun, setIsDryRun] = useState(true);

  // دریافت سفارشات آماده ارسال
  const { data: orders = [], isLoading } = useQuery<Order[]>({
    queryKey: ['ready-orders'],
    queryFn: async () => {
      const res = await fetch('http://localhost:8000/api/sms/ready-orders');
      if (!res.ok) throw new Error('خطا در دریافت سفارشات');
      return res.json();
    },
  });

  // ارسال پیامک
  const sendSMS = useMutation({
    mutationFn: async (orderIds: string[]) => {
      const res = await fetch('http://localhost:8000/api/sms/send', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ orderIds, dryRun: isDryRun }),
      });
      if (!res.ok) throw new Error('خطا در ارسال پیامک');
      return res.json();
    },
    onSuccess: () => {
      alert('پیامک‌ها با موفقیت ارسال شدند');
      setSelectedOrders([]);
    },
  });

  const handleSelectAll = () => {
    if (selectedOrders.length === orders.length) {
      setSelectedOrders([]);
    } else {
      setSelectedOrders(orders.map((o) => o.orderId));
    }
  };

  const handleToggleOrder = (orderId: string) => {
    setSelectedOrders((prev) =>
      prev.includes(orderId)
        ? prev.filter((id) => id !== orderId)
        : [...prev, orderId]
    );
  };

  if (isLoading) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600"></div>
      </div>
    );
  }

  return (
    <div className="container mx-auto p-6 max-w-7xl" dir="rtl">
      <div className="mb-8">
        <h1 className="text-3xl font-bold mb-2">📱 مدیریت ارسال پیامک</h1>
        <p className="text-gray-600">
          ارسال خودکار پیامک کد رهگیری به مشتریان
        </p>
      </div>

      {/* آمار */}
      <div className="grid gap-6 mb-6 md:grid-cols-3">
        <div className="rounded-lg border border-gray-200 bg-white shadow-sm p-6">
          <h3 className="text-lg font-semibold mb-2">کل سفارشات</h3>
          <p className="text-3xl font-bold">{orders.length}</p>
        </div>

        <div className="rounded-lg border border-gray-200 bg-white shadow-sm p-6">
          <h3 className="text-lg font-semibold mb-2">انتخاب شده</h3>
          <p className="text-3xl font-bold text-blue-600">
            {selectedOrders.length}
          </p>
        </div>

        <div className="rounded-lg border border-gray-200 bg-white shadow-sm p-6">
          <h3 className="text-lg font-semibold mb-2">آماده ارسال</h3>
          <p className="text-3xl font-bold text-green-600">
            {orders.filter((o) => o.trackingCode).length}
          </p>
        </div>
      </div>

      {/* کنترل‌ها */}
      <div className="rounded-lg border border-gray-200 bg-white shadow-sm p-6 mb-6">
        <h2 className="text-xl font-bold mb-4">🚀 ارسال خودکار</h2>
        <p className="text-gray-600 mb-4">
          ارسال پیامک برای محموله‌های جدید
        </p>

        <div className="space-y-4">
          <div className="flex items-center space-x-4 space-x-reverse">
            <input
              type="checkbox"
              checked={isDryRun}
              onChange={(e) => setIsDryRun(e.target.checked)}
              className="w-4 h-4"
              id="dryrun"
            />
            <label htmlFor="dryrun" className="text-sm cursor-pointer">
              ✅ فقط شبیه‌سازی کن (Dry Run)
            </label>
          </div>

          <div className="flex gap-2">
            <button
              onClick={handleSelectAll}
              className="px-4 py-2 bg-gray-200 rounded hover:bg-gray-300 transition"
            >
              {selectedOrders.length === orders.length
                ? 'لغو انتخاب همه'
                : 'انتخاب همه'}
            </button>

            <button
              onClick={() => sendSMS.mutate(selectedOrders)}
              disabled={selectedOrders.length === 0 || sendSMS.isPending}
              className="px-6 py-2 bg-blue-600 text-white rounded hover:bg-blue-700 disabled:bg-gray-300 disabled:cursor-not-allowed transition"
            >
              {sendSMS.isPending
                ? 'در حال ارسال...'
                : `ارسال پیامک (${selectedOrders.length})`}
            </button>
          </div>
        </div>
      </div>

      {/* جدول سفارشات */}
      <div className="rounded-lg border border-gray-200 bg-white shadow-sm p-6">
        <h2 className="text-xl font-bold mb-4">لیست سفارشات</h2>

        {orders.length === 0 ? (
          <div className="text-center py-12 text-gray-500">
            <p className="text-lg">
              هیچ سفارش جدیدی برای ارسال پیامک وجود ندارد
            </p>
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full">
              <thead className="bg-gray-50">
                <tr>
                  <th className="p-3 text-right">
                    <input
                      type="checkbox"
                      checked={
                        orders.length > 0 &&
                        selectedOrders.length === orders.length
                      }
                      onChange={handleSelectAll}
                    />
                  </th>
                  <th className="p-3 text-right">کد سفارش</th>
                  <th className="p-3 text-right">نام مشتری</th>
                  <th className="p-3 text-right">شماره تلفن</th>
                  <th className="p-3 text-right">کد رهگیری</th>
                  <th className="p-3 text-right">وضعیت</th>
                </tr>
              </thead>
              <tbody>
                {orders.map((order) => (
                  <tr
                    key={order.orderId}
                    className="border-b hover:bg-gray-50"
                  >
                    <td className="p-3">
                      <input
                        type="checkbox"
                        checked={selectedOrders.includes(order.orderId)}
                        onChange={() => handleToggleOrder(order.orderId)}
                      />
                    </td>
                    <td className="p-3 font-mono">{order.orderId}</td>
                    <td className="p-3">{order.customerName}</td>
                    <td className="p-3 font-mono direction-ltr text-left">
                      {order.phoneNumber}
                    </td>
                    <td className="p-3 font-mono text-sm">
                      {order.trackingCode}
                    </td>
                    <td className="p-3">
                      <span className="px-2 py-1 bg-green-100 text-green-800 rounded text-xs">
                        {order.status}
                      </span>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </div>
  );
}