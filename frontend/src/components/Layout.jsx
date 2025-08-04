import Navbar from './Navbar';

export default function Layout({ children }) {
  return (
    <div className="min-h-screen bg-white text-gray-800">
      <Navbar />
      <main>{children}</main>
      <footer className="bg-brand-blue text-white py-6 mt-16">
        <div className="container text-center">
          <p>&copy; {new Date().getFullYear()} CAPE·GPT. Made with ❤️ by Gen Alpha Vibes!</p>
        </div>
      </footer>
    </div>
  );
}