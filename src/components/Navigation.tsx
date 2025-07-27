import { useState } from 'react';
import { Link, useLocation, useNavigate } from 'react-router-dom';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Coffee, Home, ShoppingCart, MessageCircle, Menu, X, LogOut, User } from 'lucide-react';
import { isLoggedIn } from '@/lib/utils';

interface NavigationProps {
  cartItemCount?: number;
  onChatToggle: () => void;
  onLogout: () => void;
}

const Navigation = ({ cartItemCount = 0, onChatToggle, onLogout }: NavigationProps) => {
  const [isMenuOpen, setIsMenuOpen] = useState(false);
  const location = useLocation();
  const navigate = useNavigate();

  const isActive = (path: string) => location.pathname === path;
  
  const loggedIn = isLoggedIn();

  const handleLogout = () => {
    localStorage.removeItem('token');
    localStorage.removeItem('user_id');
    localStorage.removeItem('session_id'); // Clear session_id so a new one is generated
    navigate('/login');
  };

  const renderAuthLinks = () => {
    if (loggedIn) {
      return (
        <>
          <Button
            onClick={handleLogout}
            variant="ghost"
            className="flex items-center space-x-1 px-3 py-2 rounded-lg transition-colors hover:bg-destructive hover:text-destructive-foreground"
          >
            <LogOut className="h-4 w-4" />
            <span>Logout</span>
          </Button>
        </>
      );
    } else {
      return (
        <>
          <Link
            to="/login"
            className={`flex items-center space-x-1 px-3 py-2 rounded-lg transition-colors ${
              isActive('/login') ? 'bg-primary text-primary-foreground' : 'hover:bg-muted'
            }`}
          >
            <User className="h-4 w-4" />
            <span>Login</span>
          </Link>
          <Link
            to="/register"
            className={`flex items-center space-x-1 px-3 py-2 rounded-lg transition-colors ${
              isActive('/register') ? 'bg-primary text-primary-foreground' : 'hover:bg-muted'
            }`}
          >
            <span>Register</span>
          </Link>
        </>
      );
    }
  };

  const renderMobileAuthLinks = () => {
    if (loggedIn) {
      return (
        <Button
          onClick={handleLogout}
          variant="ghost"
          className="flex items-center space-x-2 px-3 py-2 rounded-lg transition-colors hover:bg-destructive hover:text-destructive-foreground w-full justify-start"
        >
          <LogOut className="h-4 w-4" />
          <span>Logout</span>
        </Button>
      );
    } else {
      return (
        <>
          <Link
            to="/login"
            className={`flex items-center space-x-2 px-3 py-2 rounded-lg transition-colors ${
              isActive('/login') ? 'bg-primary text-primary-foreground' : 'hover:bg-muted'
            }`}
            onClick={() => setIsMenuOpen(false)}
          >
            <User className="h-4 w-4" />
            <span>Login</span>
          </Link>
          <Link
            to="/register"
            className={`flex items-center space-x-2 px-3 py-2 rounded-lg transition-colors ${
              isActive('/register') ? 'bg-primary text-primary-foreground' : 'hover:bg-muted'
            }`}
            onClick={() => setIsMenuOpen(false)}
          >
            <span>Register</span>
          </Link>
        </>
      );
    }
  };

  return (
    <nav className="sticky top-0 z-40 w-full border-b bg-background/95 backdrop-blur supports-[backdrop-filter]:bg-background/60">
      <div className="container mx-auto px-4">
        <div className="flex h-16 items-center justify-between">
          {/* Logo */}
          <Link to="/" className="flex items-center space-x-2 text-xl font-bold">
            <Coffee className="h-8 w-8 text-primary" />
            <span className="bg-gradient-to-r from-primary to-accent bg-clip-text text-transparent">
              BrewMaster
            </span>
          </Link>

          {/* Desktop Navigation */}
          <div className="hidden md:flex items-center space-x-6">
            <Link
              to="/"
              className={`flex items-center space-x-1 px-3 py-2 rounded-lg transition-colors ${
                isActive('/') ? 'bg-primary text-primary-foreground' : 'hover:bg-muted'
              }`}
            >
              <Home className="h-4 w-4" />
              <span>Home</span>
            </Link>
            
            {loggedIn && (
            <Link
              to="/cart"
              className={`flex items-center space-x-1 px-3 py-2 rounded-lg transition-colors relative ${
                isActive('/cart') ? 'bg-primary text-primary-foreground' : 'hover:bg-muted'
              }`}
            >
              <ShoppingCart className="h-4 w-4" />
              <span>Cart</span>
              {cartItemCount > 0 && (
                <Badge className="absolute -top-1 -right-1 bg-accent text-accent-foreground text-xs min-w-5 h-5">
                  {cartItemCount}
                </Badge>
              )}
            </Link>
            )}
            {renderAuthLinks()}
          </div>

          {/* Chat Button & Mobile Menu */}
          <div className="flex items-center space-x-2">
            <Button
              onClick={onChatToggle}
              variant="outline"
              size="sm"
              className="flex items-center space-x-1 hover:bg-primary hover:text-primary-foreground transition-colors"
            >
              <MessageCircle className="h-4 w-4" />
              <span className="hidden sm:inline">Chat</span>
            </Button>

            {/* Mobile menu button */}
            <Button
              variant="ghost"
              size="sm"
              className="md:hidden"
              onClick={() => setIsMenuOpen(!isMenuOpen)}
            >
              {isMenuOpen ? <X className="h-5 w-5" /> : <Menu className="h-5 w-5" />}
            </Button>
          </div>
        </div>

        {/* Mobile Navigation */}
        {isMenuOpen && (
          <div className="md:hidden py-4 border-t">
            <div className="flex flex-col space-y-2">
              <Link
                to="/"
                className={`flex items-center space-x-2 px-3 py-2 rounded-lg transition-colors ${
                  isActive('/') ? 'bg-primary text-primary-foreground' : 'hover:bg-muted'
                }`}
                onClick={() => setIsMenuOpen(false)}
              >
                <Home className="h-4 w-4" />
                <span>Home</span>
              </Link>
              
              {loggedIn && (
              <Link
                to="/cart"
                className={`flex items-center space-x-2 px-3 py-2 rounded-lg transition-colors ${
                  isActive('/cart') ? 'bg-primary text-primary-foreground' : 'hover:bg-muted'
                }`}
                onClick={() => setIsMenuOpen(false)}
              >
                <ShoppingCart className="h-4 w-4" />
                <span>Cart</span>
                {cartItemCount > 0 && (
                  <Badge className="bg-accent text-accent-foreground text-xs">
                    {cartItemCount}
                  </Badge>
                )}
              </Link>
              )}
              {renderMobileAuthLinks()}
            </div>
          </div>
        )}
      </div>
    </nav>
  );
};

export default Navigation;
