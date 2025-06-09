#!/usr/bin/env python
# -*- coding: utf-8 -*-

import wmi
import customtkinter as ctk
from tkinter import messagebox

# Configuration de CustomTkinter
ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue")

class IPChangerApp(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("IP Changer Pro")
        self.geometry("450x430")
        self.resizable(False, False)
        
        # Liste des interfaces réseau
        self.interfaces = self.get_network_interfaces()
        self.selected_interface = ctk.StringVar()
        
        self.create_widgets()
        self.populate_interface_info()

    def get_network_interfaces(self):
        interfaces = []
        nic_configs = wmi.WMI().Win32_NetworkAdapterConfiguration(IPEnabled=True)
        for idx, nic in enumerate(nic_configs):
            interfaces.append((idx, nic.Description))
        return interfaces

    def create_widgets(self):
        # Frame principale
        main_frame = ctk.CTkFrame(self)
        main_frame.pack(pady=20, padx=20, fill="both", expand=True)

        # Sélection interface réseau
        ctk.CTkLabel(main_frame, text="Interface réseau:").pack(pady=3)
        self.interface_combo = ctk.CTkComboBox(
            main_frame,
            values=[desc for _, desc in self.interfaces],
            variable=self.selected_interface,
            command=self.on_interface_change,
            width = 300  # <-- Ajuste la largeur ici
        )
        self.interface_combo.pack(pady=5)
        if self.interfaces:
            self.interface_combo.set(self.interfaces[0][1])
        else:
            self.interface_combo.set("Aucune interface détectée")

        # Radio buttons
        self.var_radio = ctk.StringVar(value="dhcp")
        radio_frame = ctk.CTkFrame(main_frame)
        radio_frame.pack(pady=10)
        
        ctk.CTkRadioButton(
            radio_frame, 
            text="DHCP Automatique", 
            variable=self.var_radio, 
            value="dhcp",
            command=self.toggle_entries
        ).grid(row=0, column=0, padx=5, pady=5)
        
        ctk.CTkRadioButton(
            radio_frame, 
            text="Configuration Statique", 
            variable=self.var_radio, 
            value="static",
            command=self.toggle_entries
        ).grid(row=0, column=1, padx=5, pady=5)

        # Entrées de configuration
        self.entries_frame = ctk.CTkFrame(main_frame)
        self.entries_frame.pack(pady=10, fill="x")
        
        entry_config = [
            ("Adresse IP", "ip", "192.168.1.100"),
            ("Masque de sous-réseau", "subnet", "255.255.255.0"),
            ("Passerelle", "gateway", "192.168.1.1"),
            ("DNS (séparés par -)", "dns", "8.8.8.8 - 8.8.4.4")
        ]
        
        self.entries = {}
        for idx, (label, name, default) in enumerate(entry_config):
            ctk.CTkLabel(self.entries_frame, text=label).grid(row=idx, column=0, padx=5, pady=5)
            entry = ctk.CTkEntry(self.entries_frame)
            entry.insert(0, default)
            entry.grid(row=idx, column=1, padx=5, pady=5)
            self.entries[name] = entry

        # Bouton d'action
        ctk.CTkButton(
            main_frame, 
            text="Appliquer la configuration", 
            command=self.apply_configuration,
            fg_color="#308a42",
            hover_color="#1f5a2b"
        ).pack(pady=20)

        self.toggle_entries()  # Pour désactiver les champs si DHCP

    def on_interface_change(self, event=None):
        # Met à jour les champs avec la config de l'interface sélectionnée
        try:
            interface_index = next((idx for idx, desc in self.interfaces if desc == self.selected_interface.get()), None)
            if interface_index is not None:
                nic = wmi.WMI().Win32_NetworkAdapterConfiguration(IPEnabled=True)[interface_index]
                if nic.IPAddress:
                    self.entries["ip"].delete(0, "end")
                    self.entries["ip"].insert(0, nic.IPAddress[0])
                else:
                    self.entries["ip"].delete(0, "end")
                if nic.IPSubnet:
                    self.entries["subnet"].delete(0, "end")
                    self.entries["subnet"].insert(0, nic.IPSubnet[0])
                else:
                    self.entries["subnet"].delete(0, "end")
                if nic.DefaultIPGateway:
                    self.entries["gateway"].delete(0, "end")
                    self.entries["gateway"].insert(0, nic.DefaultIPGateway[0])
                else:
                    self.entries["gateway"].delete(0, "end")
                if nic.DNSServerSearchOrder:
                    self.entries["dns"].delete(0, "end")
                    self.entries["dns"].insert(0, " - ".join(nic.DNSServerSearchOrder))
                else:
                    self.entries["dns"].delete(0, "end")
        except Exception as e:
            messagebox.showwarning("Info", f"Impossible de charger la config actuelle: {str(e)}")

    def populate_interface_info(self):
        # Pré-remplir avec les infos de la première interface
        if self.interfaces:
            self.selected_interface.set(self.interfaces[0][1])
            self.on_interface_change()

    def toggle_entries(self):
        state = "normal" if self.var_radio.get() == "static" else "disabled"
        for entry in self.entries.values():
            entry.configure(state=state)

    def validate_entries(self):
        # Validation basique des entrées
        if self.var_radio.get() == "static":
            for name, entry in self.entries.items():
                if not entry.get().strip():
                    messagebox.showerror("Erreur", f"Le champ {name} ne peut pas être vide")
                    return False
        return True

    def apply_configuration(self):
        if not self.validate_entries():
            return
            
        interface_index = next((idx for idx, desc in self.interfaces if desc == self.selected_interface.get()), None)
        
        if interface_index is None:
            messagebox.showerror("Erreur", "Aucune interface sélectionnée")
            return
            
        try:
            if self.var_radio.get() == "dhcp":
                success = self.set_dhcp(interface_index)
            else:
                success = self.set_static_ip(interface_index)
                
            if success:
                messagebox.showinfo("Succès", "Configuration appliquée avec succès")
            else:
                messagebox.showerror("Erreur", "Échec de la configuration")
                
        except Exception as e:
            messagebox.showerror("Erreur", f"Une erreur est survenue:\n{str(e)}")

    def set_dhcp(self, interface_index):
        nic = wmi.WMI().Win32_NetworkAdapterConfiguration(IPEnabled=True)[interface_index]
        # Active le DHCP pour l'adresse IP
        dhcp_result = nic.EnableDHCP()[0]
        # Réinitialise les DNS pour qu'ils soient obtenus automatiquement
        dns_result = nic.SetDNSServerSearchOrder()[0]
        return dhcp_result == 0 and dns_result == 0

    def set_static_ip(self, interface_index):
        nic = wmi.WMI().Win32_NetworkAdapterConfiguration(IPEnabled=True)[interface_index]
        
        ip = self.entries["ip"].get()
        subnet = self.entries["subnet"].get()
        gateway = self.entries["gateway"].get()
        dns_servers = self.entries["dns"].get().split(" - ")
        
        results = [
            nic.EnableStatic(IPAddress=[ip], SubnetMask=[subnet])[0],
            nic.SetGateways(DefaultIPGateway=[gateway])[0],
            nic.SetDNSServerSearchOrder(dns_servers)[0]
        ]
        
        return all(result == 0 for result in results)

if __name__ == "__main__":
    app = IPChangerApp()
    app.mainloop()
