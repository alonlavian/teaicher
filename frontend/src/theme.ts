import { extendTheme, type ThemeConfig } from '@chakra-ui/react'

const config: ThemeConfig = {
  initialColorMode: 'light',
  useSystemColorMode: true,
}

const theme = extendTheme({
  config,
  fonts: {
    heading: 'Rubik, system-ui, sans-serif',
    body: 'Rubik, system-ui, sans-serif',
  },
  styles: {
    global: {
      'html, body': {
        minHeight: '100vh',
        backgroundColor: 'gray.50',
        _dark: {
          backgroundColor: 'gray.800',
        },
      },
    },
  },
  components: {
    Button: {
      defaultProps: {
        colorScheme: 'blue',
      },
    },
  },
})

export default theme
