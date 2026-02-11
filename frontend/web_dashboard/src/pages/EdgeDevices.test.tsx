/**
 * Edge Devices Component Tests
 * Comprehensive test suite for the EdgeDevices component
 */

import React from 'react'
import { render, screen, fireEvent, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import EdgeDevices from './EdgeDevices'
import { edgeDeviceService } from '../services/edgeDeviceService'

// Mock the API service
jest.mock('../services/edgeDeviceService')
jest.mock('../components/AppLayout', () => {
  return function MockAppLayout({ children }: { children: React.ReactNode }) {
    return <div>{children}</div>
  }
})

describe('EdgeDevices Component', () => {
  beforeEach(() => {
    jest.clearAllMocks()
  })

  const mockDevices = [
    {
      id: 'edge-001',
      name: 'Atlas-500-East',
      platform: 'atlas',
      status: 'online',
      cpu_usage: 45,
      memory_usage: 62,
      temperature: 52,
      uptime: 328,
      last_seen: new Date().toISOString(),
      firmware_version: '2.1.0',
      tee_enabled: true,
      tpm_attestation: true,
      location: 'DataCenter-US-East',
      model: 'Atlas 500',
      cores: 64,
      memory_gb: 256,
    },
    {
      id: 'edge-002',
      name: 'Kunpeng-920-Central',
      platform: 'hisilicon',
      status: 'online',
      cpu_usage: 38,
      memory_usage: 54,
      temperature: 48,
      uptime: 422,
      last_seen: new Date(Date.now() - 30000).toISOString(),
      firmware_version: '1.9.2',
      tee_enabled: true,
      tpm_attestation: true,
      location: 'DataCenter-EU-Central',
      model: 'Kunpeng 920',
      cores: 128,
      memory_gb: 512,
    },
  ]

  describe('Rendering', () => {
    it('should render the component with header', () => {
      ; (edgeDeviceService.getDevices as jest.Mock).mockResolvedValue(mockDevices)

      render(<EdgeDevices />)

      expect(screen.getByText('Edge Device Management')).toBeInTheDocument()
      expect(screen.getByText('Distributed Trusted Execution Environment Network')).toBeInTheDocument()
    })

    it('should render view mode tabs', () => {
      ; (edgeDeviceService.getDevices as jest.Mock).mockResolvedValue(mockDevices)

      render(<EdgeDevices />)

      expect(screen.getByText('Grid View')).toBeInTheDocument()
      expect(screen.getByText('List View')).toBeInTheDocument()
      expect(screen.getByText('Security')).toBeInTheDocument()
    })

    it('should render stats cards with correct initial values', async () => {
      ; (edgeDeviceService.getDevices as jest.Mock).mockResolvedValue(mockDevices)

      render(<EdgeDevices />)

      await waitFor(() => {
        expect(screen.getByText('Total Devices')).toBeInTheDocument()
        expect(screen.getByText('Secure Devices')).toBeInTheDocument()
        expect(screen.getByText('Device Binding')).toBeInTheDocument()
        expect(screen.getByText('Encryption')).toBeInTheDocument()
      })
    })
  })

  describe('Device Loading', () => {
    it('should load devices on component mount', async () => {
      ; (edgeDeviceService.getDevices as jest.Mock).mockResolvedValue(mockDevices)

      render(<EdgeDevices />)

      await waitFor(() => {
        expect(edgeDeviceService.getDevices).toHaveBeenCalled()
      })
    })

    it('should display device names in grid view', async () => {
      ; (edgeDeviceService.getDevices as jest.Mock).mockResolvedValue(mockDevices)

      render(<EdgeDevices />)

      await waitFor(() => {
        expect(screen.getByText('Atlas-500-East')).toBeInTheDocument()
        expect(screen.getByText('Kunpeng-920-Central')).toBeInTheDocument()
      })
    })

    it('should display device metrics correctly', async () => {
      ; (edgeDeviceService.getDevices as jest.Mock).mockResolvedValue(mockDevices)

      render(<EdgeDevices />)

      await waitFor(() => {
        // Check CPU usage for first device
        expect(screen.getByText('45%')).toBeInTheDocument()
        // Check memory usage
        expect(screen.getByText('62%')).toBeInTheDocument()
      })
    })

    it('should handle API errors gracefully', async () => {
      const error = new Error('API Error')
        ; (edgeDeviceService.getDevices as jest.Mock).mockRejectedValue(error)

      render(<EdgeDevices />)

      await waitFor(() => {
        // Component should not crash and should display gracefully
        expect(screen.getByText('Edge Device Management')).toBeInTheDocument()
      })
    })
  })

  describe('View Mode Switching', () => {
    beforeEach(() => {
      ; (edgeDeviceService.getDevices as jest.Mock).mockResolvedValue(mockDevices)
    })

    it('should switch to list view when clicking List View tab', async () => {
      render(<EdgeDevices />)

      const listViewTab = screen.getByText('List View')
      fireEvent.click(listViewTab)

      await waitFor(() => {
        expect(listViewTab).toHaveClass('bg-cyan-500/20')
      })
    })

    it('should switch to security view when clicking Security tab', async () => {
      render(<EdgeDevices />)

      const securityTab = screen.getByText('Security')
      fireEvent.click(securityTab)

      await waitFor(() => {
        expect(securityTab).toHaveClass('bg-cyan-500/20')
      })
    })
  })

  describe('Device Selection', () => {
    beforeEach(() => {
      ; (edgeDeviceService.getDevices as jest.Mock).mockResolvedValue(mockDevices)
    })

    it('should select device when clicking on device card', async () => {
      render(<EdgeDevices />)

      await waitFor(() => {
        const deviceCard = screen.getByText('Atlas-500-East').closest('div')
        if (deviceCard) {
          fireEvent.click(deviceCard)
        }
      })

      await waitFor(() => {
        expect(screen.getByText('Atlas-500-East Details')).toBeInTheDocument()
      })
    })

    it('should display device details panel when device is selected', async () => {
      render(<EdgeDevices />)

      await waitFor(() => {
        const deviceCard = screen.getByText('Atlas-500-East').closest('div')
        if (deviceCard) {
          fireEvent.click(deviceCard)
        }
      })

      await waitFor(() => {
        expect(screen.getByText('CPU Trend')).toBeInTheDocument()
        expect(screen.getByText('Memory Trend')).toBeInTheDocument()
        expect(screen.getByText('Temperature Trend')).toBeInTheDocument()
      })
    })
  })

  describe('Filtering', () => {
    beforeEach(() => {
      ; (edgeDeviceService.getDevices as jest.Mock).mockResolvedValue(mockDevices)
    })

    it('should toggle filter panel when clicking Filters button', async () => {
      render(<EdgeDevices />)

      const filterButton = screen.getByText('Filters')
      fireEvent.click(filterButton)

      await waitFor(() => {
        expect(screen.getByDisplayValue('All Platforms')).toBeInTheDocument()
      })
    })

    it('should filter devices by platform', async () => {
      render(<EdgeDevices />)

      const filterButton = screen.getByText('Filters')
      fireEvent.click(filterButton)

      const platformSelect = screen.getByDisplayValue('All Platforms')
      await userEvent.selectOptions(platformSelect, 'atlas')

      await waitFor(() => {
        expect(screen.getByText('Atlas-500-East')).toBeInTheDocument()
        // Kunpeng device should not be visible
      })
    })

    it('should filter devices by status', async () => {
      const degradedDevice = { ...mockDevices[0], status: 'degraded' }
        ; (edgeDeviceService.getDevices as jest.Mock).mockResolvedValue([...mockDevices, degradedDevice])

      render(<EdgeDevices />)

      const filterButton = screen.getByText('Filters')
      fireEvent.click(filterButton)

      const statusSelect = screen.getByDisplayValue('All Status')
      await userEvent.selectOptions(statusSelect, 'online')

      await waitFor(() => {
        // Only online devices should be shown
        expect(screen.getByText('Atlas-500-East')).toBeInTheDocument()
      })
    })

    it('should filter devices by TEE status', async () => {
      render(<EdgeDevices />)

      const filterButton = screen.getByText('Filters')
      fireEvent.click(filterButton)

      const teeSelect = screen.getByDisplayValue('All Devices')
      await userEvent.selectOptions(teeSelect, 'enabled')

      await waitFor(() => {
        // Only devices with TEE enabled should be shown
        expect(screen.getByText('Atlas-500-East')).toBeInTheDocument()
      })
    })
  })

  describe('Remote Commands', () => {
    beforeEach(() => {
      ; (edgeDeviceService.getDevices as jest.Mock).mockResolvedValue(mockDevices)
    })

    it('should execute status command when clicking Status button', async () => {
      ; (edgeDeviceService.executeRemoteCommand as jest.Mock).mockResolvedValue({
        success: true,
        device_id: 'edge-001',
        command: 'status',
        result: 'Device online',
        timestamp: new Date().toISOString(),
      })

      render(<EdgeDevices />)

      await waitFor(() => {
        const statusButtons = screen.getAllByText('Status')
        fireEvent.click(statusButtons[0])
      })

      await waitFor(() => {
        expect(edgeDeviceService.executeRemoteCommand).toHaveBeenCalledWith('edge-001', 'status')
      })
    })

    it('should execute reboot command when clicking Reboot button', async () => {
      ; (edgeDeviceService.executeRemoteCommand as jest.Mock).mockResolvedValue({
        success: true,
        device_id: 'edge-001',
        command: 'reboot',
        timestamp: new Date().toISOString(),
      })

      render(<EdgeDevices />)

      await waitFor(() => {
        const rebootButtons = screen.getAllByText('Reboot')
        fireEvent.click(rebootButtons[0])
      })

      await waitFor(() => {
        expect(edgeDeviceService.executeRemoteCommand).toHaveBeenCalledWith('edge-001', 'reboot')
      })
    })

    it('should disable buttons while command is executing', async () => {
      ; (edgeDeviceService.executeRemoteCommand as jest.Mock).mockImplementation(
        () => new Promise((resolve) => setTimeout(resolve, 1000))
      )

      render(<EdgeDevices />)

      await waitFor(() => {
        const statusButtons = screen.getAllByText('Status')
        fireEvent.click(statusButtons[0])
      })

      await waitFor(() => {
        const statusButtons = screen.getAllByText('Status')
        expect(statusButtons[0]).toBeDisabled()
      })
    })
  })

  describe('Status Indicators', () => {
    beforeEach(() => {
      ; (edgeDeviceService.getDevices as jest.Mock).mockResolvedValue(mockDevices)
    })

    it('should display correct status color for online devices', async () => {
      render(<EdgeDevices />)

      await waitFor(() => {
        const statusElements = screen.getAllByText('Online')
        expect(statusElements[0]).toHaveClass('text-green-400')
      })
    })

    it('should display correct status color for offline devices', async () => {
      const offlineDevice = { ...mockDevices[0], status: 'offline' }
        ; (edgeDeviceService.getDevices as jest.Mock).mockResolvedValue([offlineDevice])

      render(<EdgeDevices />)

      await waitFor(() => {
        const offlineStatus = screen.getByText('Offline')
        expect(offlineStatus).toHaveClass('text-red-400')
      })
    })

    it('should display security status indicators', async () => {
      render(<EdgeDevices />)

      await waitFor(() => {
        // Check for TEE and TPM indicators
        const checkIcons = screen.getAllByRole('img')
        expect(checkIcons.length).toBeGreaterThan(0)
      })
    })
  })

  describe('Temperature Warnings', () => {
    it('should show temperature warning for critical temperatures', async () => {
      const hotDevice = { ...mockDevices[0], temperature: 85 }
        ; (edgeDeviceService.getDevices as jest.Mock).mockResolvedValue([hotDevice])

      render(<EdgeDevices />)

      await waitFor(() => {
        const tempText = screen.getByText('85°C')
        expect(tempText).toHaveClass('text-red-400')
      })
    })

    it('should show normal temperature for safe temperatures', async () => {
      const coolDevice = { ...mockDevices[0], temperature: 45 }
        ; (edgeDeviceService.getDevices as jest.Mock).mockResolvedValue([coolDevice])

      render(<EdgeDevices />)

      await waitFor(() => {
        const tempText = screen.getByText('45°C')
        expect(tempText).toHaveClass('text-green-400')
      })
    })
  })

  describe('Security View', () => {
    beforeEach(() => {
      ; (edgeDeviceService.getDevices as jest.Mock).mockResolvedValue(mockDevices)
    })

    it('should display security metrics cards', async () => {
      render(<EdgeDevices />)

      const securityTab = screen.getByText('Security')
      fireEvent.click(securityTab)

      await waitFor(() => {
        expect(screen.getByText(/Trusted Execution Environments/i)).toBeInTheDocument()
        expect(screen.getByText(/TPM & Attestation/i)).toBeInTheDocument()
        expect(screen.getByText(/Encryption & Privacy/i)).toBeInTheDocument()
      })
    })

    it('should display compliance scores', async () => {
      render(<EdgeDevices />)

      const securityTab = screen.getByText('Security')
      fireEvent.click(securityTab)

      await waitFor(() => {
        // Check for percentage indicators
        const percentTexts = screen.getAllByText(/\d+%/)
        expect(percentTexts.length).toBeGreaterThan(0)
      })
    })
  })

  describe('Responsive Design', () => {
    it('should render properly on mobile devices', () => {
      ; (edgeDeviceService.getDevices as jest.Mock).mockResolvedValue(mockDevices)

      const { container } = render(<EdgeDevices />)

      // Check for mobile-responsive classes
      const gridContainer = container.querySelector('.grid')
      expect(gridContainer).toBeInTheDocument()
    })
  })

  describe('Auto-refresh', () => {
    it('should refresh devices periodically', async () => {
      jest.useFakeTimers()
        ; (edgeDeviceService.getDevices as jest.Mock).mockResolvedValue(mockDevices)

      render(<EdgeDevices />)

      expect(edgeDeviceService.getDevices).toHaveBeenCalledTimes(1)

      jest.advanceTimersByTime(5000)

      expect(edgeDeviceService.getDevices).toHaveBeenCalledTimes(2)

      jest.advanceTimersByTime(5000)

      expect(edgeDeviceService.getDevices).toHaveBeenCalledTimes(3)

      jest.useRealTimers()
    })

    it('should clean up interval on component unmount', async () => {
      ; (edgeDeviceService.getDevices as jest.Mock).mockResolvedValue(mockDevices)

      const { unmount } = render(<EdgeDevices />)

      const intervalSpy = jest.spyOn(global, 'setInterval')
      unmount()

      expect(intervalSpy).toHaveBeenCalled()
    })
  })

  describe('Search Functionality', () => {
    beforeEach(() => {
      ; (edgeDeviceService.getDevices as jest.Mock).mockResolvedValue(mockDevices)
    })

    it('should filter devices by search term', async () => {
      render(<EdgeDevices />)

      const searchInput = screen.getByPlaceholderText('Search devices...')
      await userEvent.type(searchInput, 'Atlas')

      await waitFor(() => {
        expect(screen.getByText('Atlas-500-East')).toBeInTheDocument()
      })
    })
  })
})
