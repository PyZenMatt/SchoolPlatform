const navigation = {
  items: [
    {
      id: 'navigation',
      title: 'Navigazione',
      type: 'group',
      icon: 'icon-navigation',
      children: [
        {
          id: 'dashboard',
          title: 'Dashboard',
          type: 'item',
          url: '/dashboard/student',
          icon: 'feather icon-home'
        },
        {
          id: 'courses',
          title: 'Corsi',
          type: 'item',
          url: '/corsi',
          icon: 'feather icon-book-open'
        },
        {
          id: 'wallet',
          title: 'Wallet',
          type: 'item',
          url: '/test/rewards',
          icon: 'feather icon-credit-card'
        },
        {
          id: 'profile',
          title: 'Profilo',
          type: 'item',
          url: '/profile',
          icon: 'feather icon-user'
        }
      ]
    }
  ]
};

export default navigation;
