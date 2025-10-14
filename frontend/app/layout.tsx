import './globals.css'

export const metadata = {
  title: 'سیستم مدیریت دیجی‌کالا',
  description: 'داشبورد مدیریت سفارشات',
}

export default function RootLayout({
  children,
}: {
  children: React.ReactNode
}) {
  return (
    <html lang="fa" dir="rtl">
      <body>{children}</body>
    </html>
  )
}