// frontend/app/sms/page.tsx
'use client';

import { useState, useEffect } from 'react';
import { MessageSquare, Send, CheckCircle, XCircle, Smartphone, AlertCircle, RefreshCw } from 'lucide-react';

interface Order {
  id: number;
  orderId: string;
  customerName: string;
  trackingCode: string;
  phoneNumber: string;
  status: string;
  shipmentId: string;
}

interface SMSStatus {
  kde_connect_installed: boolean;
  device_connected: boolean;
  status_message: string;
  device_id: string;
}

export default function SMSPage() {
  const [orders, setOrders] = useState<Order[]>([]);
  const [selectedOrders, setSelectedOrders] = useState<number[]>([]);
  const [isDryRun, setIsDryRun] = useState(true);
  const [loading, setLoading] = useState(true);
  const [sending, setSending] = useState(false);
  const [smsStatus, setSmsStatus] = useState<SMSStatus | null>(null);

  useEffect(() => {
    loadOrders();
    checkSMSStatus();
  }, []);

  const checkSMSStatus = async () => {
    try {
      const response = await fetch('http://localhost:8000/api/sms/status');
      const data = await response.json();
      setSmsStatus(data);
    } catch (error) {
      console.error('خطا در بررسی وضعیت:', error);
    }
  };

  const loadOrders = async () => {
    try {
      setLoading(true);
      const response = await fetch('http://localhost:8000/api/sms/ready-orders');
      const data = await response.json();
      setOrders(data);
    } catch (error) {
      console.error('خطا:', error);
      alert('خطا در دریافت سفارشات');
    } finally {
      setLoading(false);
    }
  };

  const handleSelectAll = () => {
    if (selectedOrders.length === orders.length) {
      setSelectedOrders([]);
    } else {
      setSelectedOrders(orders.map((o) => o.id));
    }
  };

  const handleToggleOrder = (orderId: number) => {
    setSelectedOrders((prev) =>
      prev.includes(orderId)
        ? prev.filter((id) => id !== orderId)
        : [...prev, orderId]
    );
  };

  const handleSendSMS = async () => {
    if (selectedOrders.length === 0) {
      alert('لطفاً حداقل یک سفارش انتخاب کنید');
      return;
    }

    if (!isDryRun && !confirm(`آیا مطمئن هستید که می‌خواهید ${selectedOrders.length} پیامک ارسال کنید؟`)) {
      return;
    }

    try {
      setSending(true);
      const response = await fetch('http://localhost:8000/api/sms/send', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          order_ids: selectedOrders,
          dry_run: isDryRun,
        }),
      });

      if (!response.ok) throw new Error('خطا در ارسال');

      const data = await response.json();
      alert(`✅ ارسال کامل شد!\n\nموفق: ${data.success}\nناموفق: ${data.failed}`);
      
      setSelectedOrders([]);
      await loadOrders();
    } catch (error) {
      alert('❌ خطا در ارسال پیامک');
    } finally {
      setSending(false);
    }
  };

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-gradient-to-br from-slate-50 to-slate-100">
        <div className="text-center">
          <div className="animate-spin rounded-full h-16 w-16 border-b-4 border-blue-600 mx-auto mb-4"></div>
          <p className="text-gray-600 text-lg">در حال بارگذاری...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-50 to-slate-100" dir="rtl">
      <header className="bg-white shadow-sm border-b sticky top-0 z-10">
        <div className="max-w-7xl mx-auto px-6 py-4">
          <div className="flex items-center gap-3">
            <a href="/" className="text-2xl hover:text-blue-600 transition">←</a>
            <div>
              <h1 className="text-2xl font-bold text-gray-900">📱 مدیریت ارسال پیامک</h1>
              <p className="text-gray-600 mt-1">ارسال خودکار پیامک کد رهگیری به مشتریان</p>
            </div>
          </div>
        </div>
      </header>

      <main className="max-w-7xl mx-auto px-6 py-8">
        {/* SMS Status */}
        <div className={`rounded-xl shadow-lg p-6 mb-6 ${
          smsStatus?.device_connected 
            ? 'bg-gradient-to-r from-green-50 to-emerald-50 border-2 border-green-200'
            : 'bg-gradient-to-r from-red-50 to-rose-50 border-2 border-red-200'
        }`}>
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-4">
              <div className={`w-16 h-16 rounded-full flex items-center justify-center ${
                smsStatus?.device_connected ? 'bg-green-100' : 'bg-red-100'
              }`}>
                <Smartphone size={32} className={smsStatus?.device_connected ? 'text-green-600' : 'text-red-600'} />
              </div>
              <div>
                <h3 className="text-lg font-bold text-gray-900">وضعیت KDE Connect</h3>
                <p className={`mt-1 ${smsStatus?.device_connected ? 'text-green-700' : 'text-red-700'}`}>
                  {smsStatus?.status_message || 'در حال بررسی...'}
                </p>
                {smsStatus?.device_id && (
                  <p className="text-sm text-gray-600 mt-1">Device ID: {smsStatus.device_id}</p>
                )}
              </div>
            </div>
            <button
              onClick={checkSMSStatus}
              className="px-4 py-2 bg-white rounded-lg hover:bg-gray-50 transition flex items-center gap-2"
            >
              <RefreshCw size={18} />
              بررسی مجدد
            </button>
          </div>
        </div>

        {/* Stats */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-6">
          <div className="bg-white rounded-xl shadow-lg p-6">
            <h3 className="text-gray-600 text-sm mb-2">کل سفارشات</h3>
            <p className="text-4xl font-bold text-gray-900">{orders.length}</p>
          </div>
          <div className="bg-white rounded-xl shadow-lg p-6">
            <h3 className="text-gray-600 text-sm mb-2">انتخاب شده</h3>
            <p className="text-4xl font-bold text-blue-600">{selectedOrders.length}</p>
          </div>
          <div className="bg-white rounded-xl shadow-lg p-6">
            <h3 className="text-gray-600 text-sm mb-2">آماده ارسال</h3>
            <p className="text-4xl font-bold text-green-600">
              {orders.filter((o) => o.trackingCode).length}
            </p>
          </div>
        </div>

        {/* Controls */}
        <div className="bg-white rounded-xl shadow-lg p-6 mb-6">
          <h2 className="text-xl font-bold mb-4">🚀 ارسال خودکار</h2>
          <div className="space-y-4">
            <div className="flex items-center gap-3">
              <input
                type="checkbox"
                checked={isDryRun}
                onChange={(e) => setIsDryRun(e.target.checked)}
                className="w-5 h-5 text-blue-600 rounded focus:ring-2 focus:ring-blue-500"
                id="dryrun"
              />
              <label htmlFor="dryrun" className="text-sm cursor-pointer">
                ✅ فقط شبیه‌سازی کن (Dry Run) - پیامک واقعی ارسال نمی‌شود
              </label>
            </div>

            <div className="flex gap-3">
              <button
                onClick={handleSelectAll}
                className="px-6 py-3 bg-gray-200 text-gray-700 rounded-lg hover:bg-gray-300 transition"
              >
                {selectedOrders.length === orders.length ? '❌ لغو انتخاب همه' : '✅ انتخاب همه'}
              </button>
              <button
                onClick={handleSendSMS}
                disabled={selectedOrders.length === 0 || sending || (!isDryRun && !smsStatus?.device_connected)}
                className="flex-1 px-6 py-3 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:bg-gray-300 disabled:cursor-not-allowed transition flex items-center justify-center gap-2"
              >
                {sending ? (
                  <>
                    <div className="animate-spin rounded-full h-5 w-5 border-b-2 border-white"></div>
                    در حال ارسال...
                  </>
                ) : (
                  <>
                    <Send size={20} />
                    ارسال پیامک ({selectedOrders.length})
                  </>
                )}
              </button>
            </div>

            {!isDryRun && !smsStatus?.device_connected && (
              <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-4">
                <div className="flex items-start gap-3">
                  <AlertCircle className="text-yellow-600 flex-shrink-0 mt-0.5" size={20} />
                  <div className="text-sm text-yellow-900">
                    <p className="font-semibold mb-1">توجه!</p>
                    <p>برای ارسال واقعی پیامک، باید KDE Connect متصل باشد.</p>
                  </div>
                </div>
              </div>
            )}
          </div>
        </div>

        {/* Orders Table */}
        <div className="bg-white rounded-xl shadow-lg p-6">
          <h2 className="text-xl font-bold mb-4">لیست سفارشات</h2>

          {orders.length === 0 ? (
            <div className="text-center py-12 text-gray-500">
              <MessageSquare size={64} className="mx-auto mb-4 text-gray-300" />
              <p className="text-lg">هیچ سفارش جدیدی برای ارسال پیامک وجود ندارد</p>
              <button onClick={loadOrders} className="mt-4 text-blue-600 hover:text-blue-700 font-medium">
                بارگذاری مجدد →
              </button>
            </div>
          ) : (
            <div className="overflow-x-auto">
              <table className="w-full text-sm">
                <thead className="bg-gray-50">
                  <tr>
                    <th className="p-3 text-right">
                      <input
                        type="checkbox"
                        checked={orders.length > 0 && selectedOrders.length === orders.length}
                        onChange={handleSelectAll}
                        className="w-4 h-4"
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
                    <tr key={order.id} className="border-b hover:bg-gray-50">
                      <td className="p-3">
                        <input
                          type="checkbox"
                          checked={selectedOrders.includes(order.id)}
                          onChange={() => handleToggleOrder(order.id)}
                          className="w-4 h-4"
                        />
                      </td>
                      <td className="p-3 font-mono text-xs">{order.orderId}</td>
                      <td className="p-3">{order.customerName}</td>
                      <td className="p-3 font-mono text-xs" dir="ltr">{order.phoneNumber}</td>
                      <td className="p-3 font-mono text-xs text-green-600">{order.trackingCode}</td>
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
      </main>
    </div>
  );
}