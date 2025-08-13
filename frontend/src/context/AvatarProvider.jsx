import { createContext, useContext, useState } from 'react';

const AvatarContext = createContext(null);

export const AvatarProvider = ({ children }) => {
  const [pack, setPack] = useState('classic');
  const [variant, setVariant] = useState('math');
  const [season, setSeason] = useState('default');

  return (
    <AvatarContext.Provider value={{ pack, setPack, variant, setVariant, season, setSeason }}>
      {children}
    </AvatarContext.Provider>
  );
};

export const useAvatar = () => {
  const context = useContext(AvatarContext);
  if (!context) {
    throw new Error('useAvatar must be used within an AvatarProvider');
  }
  return context;
};
